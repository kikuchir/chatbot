from flask import Flask, render_template, jsonify, request, redirect, send_from_directory, flash
from gensim.models import word2vec
from gensim.models import KeyedVectors
from janome.analyzer import Analyzer# 形態素解析ライブラリ 「pip install janome」
from janome.charfilter import *
from janome.tokenfilter import *
from werkzeug.utils import secure_filename
import json
import pprint
import openpyxl
import os
import sys
import numpy as np
import wordnet

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./data"

#wiki_model = KeyedVectors.load_word2vec_format('./model/jawiki2017_model.vec')
wiki_model = word2vec.Word2Vec.load('./model/latest-ja-word2vec-gensim-model/word2vec.gensim.model')# 追加学習の場合は読み取り専用のKeyedVectorsではなくWord2Vecモデルとして読み込む
#wiki_model = KeyedVectors.load_word2vec_format('./model/cc.ja.300.vec')#精度は高いけど読み込み遅い

# 問い合わせ台帳のQを追加学習
copus = word2vec.Text8Corpus('./data/split_問合せ管理表サンプル.txt')
wiki_model.build_vocab(copus, update=True)
#wiki_model.build_vocab('./data/split_問合せ管理表サンプル.txt', update=True)
wiki_model.train(copus, total_examples=wiki_model.corpus_count, epochs=wiki_model.iter)
# TODO「請求額」とかsplit_txtに存在する単語がKeyErrorになる。追加学習できていない？

# 形態素解析の設定
token_filters = [CompoundNounFilter(),# 連続する名詞の複合名詞化
                 POSKeepFilter(['名詞','形容詞']), # 抽出する品詞の指定
                 UpperCaseFilter()] # アルファベットを大文字に変換
a = Analyzer(token_filters=token_filters)
# 問い合わせ台帳の読み込み
excel_path = "./data/QA.xlsx"
wb = openpyxl.load_workbook(excel_path)
sheet = wb.worksheets[0]
q_col = "B"# 質問の列（ABC...）
a_col = "C"# 回答の列（ABC...）

# 分かち書き
def separate_word(question):
    print('■debug:「%s」を形態素解析します。' % question)
    word_list = []
    for token in a.analyze(question):
        print(str(token))
        word_list.append(str(token).split()[0])
    return word_list

# テキストのベクトルを計算
def get_vector(text):
    sum_vec = np.zeros(50)
    word_count = 0
    for token in a.analyze(text):
        try:
            #print('■debug:' + str(token).split()[0] + 'のvectorを取得')
            sum_vec += wiki_model[str(token).split()[0]]
            word_count += 1
        except KeyError:
            print('■debug:KeyError発生 ' + str(token).split()[0])
    return sum_vec / word_count

# cos類似度を計算
def cos_sim(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# エクセルを単語リストで検索
def search_question(word_list):
    row_points = []
    for i in range(200):#Excel何行目まで見るか
        point = 0
        q_cell = sheet[q_col + str(i+1)]
        a_cell = sheet[a_col + str(i+1)]
        if q_cell.value is not None and a_cell.value is not None:
            # 行番号と単語ヒット数のリスト
            for keyword in word_list:
                if keyword.casefold() in q_cell.value.casefold():# 大文字小文字区別しない
                    print('■debug:' + str(i+1) + '行目の質問に「' + keyword + '」がヒット！')
                    point += 1# 点加算 TODO 名詞がヒットしたら10点、形容詞と動詞は1点とかにしたい。
            if point > 0: row_points.append([i+1,point])
    return row_points

# 初期表示
@app.route('/')
def page_load():
    #TODO saveされたmodelをloadする(?)
    return render_template('chat.html')

# 質問を受け取って回答を返す
@app.route('/question', methods=['POST'])
def answer():
    question = request.form['question']

    # 質問を形態素解析して単語リスト（名詞、形容詞、動詞）に変換
    word_list = separate_word(question)
    
    # 問い合わせ台帳を検索
    row_points = search_question(word_list)
    #ヒットしない場合は、類義語でもう一度検索
    #TODO 毎回類義語で検索したい。加算0.5点とか
    if len(row_points) == 0 :
        synonym_word_list = []
        for word in word_list:
            synonym_word_list += wordnet.get_synonyms(word)
            pprint.pprint(synonym_word_list)
        row_points = search_question(synonym_word_list)
    
    # 関連度の高い質問と回答のセットを返却
    top_points = []
    top_row = [0,0]# [行番号,類似度]
    if len(row_points) > 0 :
        # ヒット数でソート（降順）  
        row_points.sort(key=lambda x: x[1],reverse=True)
        print('■debug:採点結果（点数の降順）')
        pprint.pprint(row_points)
        # 最高点のみに絞り込む
        top_points = [i for i in row_points if i[1] == row_points[0][1]]
        print('■debug:採点結果（最高点のみ）')
        pprint.pprint(top_points)
        # 最高点が複数存在する場合は、入力された質問とベクトル類似度が高いQAを返す
        if len(top_points) > 1:
            m_vec = get_vector(question)
            for row in top_points:
                print('■debug:q_vec ' + sheet[q_col + str(row[0])].value)
                q_vec = get_vector(sheet[q_col + str(row[0])].value)
                print('コサイン類似度：' + str(cos_sim(m_vec, q_vec)))
                if top_row[1] < cos_sim(m_vec, q_vec):
                    top_row[0] = row[0]
                    top_row[1] = cos_sim(m_vec, q_vec)
        # 最高点が1件の場合はそれを返す
        else: top_row[0] = row_points[0][0]
        print('■質問\n' + sheet[q_col + str(top_row[0])].value + '\n■回答\n' + sheet[a_col + str(top_row[0])].value)
        return_json = {
            "information":"最も関連度の高い回答はこちらです。",
            "hit_question": sheet[q_col + str(top_row[0])].value,
            "hit_answer": sheet[a_col + str(top_row[0])].value
        }
    else:# １件もヒットしない場合はsorry回答
        return_json = {
            "information":"すみません。「" + question + "」に関連する回答はありません。",
            "hit_question": "",
            "hit_answer": ""
        }
    
    return jsonify(values=json.dumps(return_json))

# 管理画面(GET)
@app.route('/admin',methods=['GET'])
def adminpage_load():
    qa_table = []
    for i in range(200):#Excel何行目まで見るか
        q_cell = sheet[q_col + str(i+1)]
        a_cell = sheet[a_col + str(i+1)]
        if q_cell.value is not None and a_cell.value is not None:
            qa_table.append([i+1,q_cell.value,a_cell.value])
    return render_template('admin.html',qa_table=qa_table)

# 管理画面(POST:Excelのアップロード)
@app.route('/admin',methods=['POST'])
def upload():
    print("upload()処理開始")
    # ファイル存在チェック
    if 'file' not in request.files:
        print("ファイルが存在しない。")
        return redirect(request.url)
    # データの取り出し
    file = request.files['file']
    filename = file.filename
    print("ファイル名：" + filename)
    # ファイル名チェック
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx','xls']:
        #filename = secure_filename(file.filename)# 危険な文字を削除（サニタイズ処理）★2バイト文字消えちゃうので一旦外す
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))# ファイルの保存
        print("upload()ファイル保存完了")
        # アップロード後のページに転送
        return redirect(request.url)
    else:
        print("ファイル名が存在しない。またはエクセル形式でない。")
        return redirect(request.url)
    #TODO アップしたエクセルを分かち書きにする
    #TODO wikiモデルに追加学習させる
    #TODO saveする


# キャッシュしない
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

## おまじない
if __name__ == "__main__":
    app.run(debug=True)