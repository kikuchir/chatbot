from janome.tokenizer import Tokenizer # 形態素解析ライブラリ 「pip install janome」
from janome.analyzer import Analyzer
from janome.charfilter import *
from janome.tokenfilter import *
from gensim.models import word2vec
import openpyxl
import os
import sys
import pprint

#t = Tokenizer()
token_filters = [CompoundNounFilter(),# 連続する名詞の複合名詞化
                 POSKeepFilter(['名詞','形容詞','動詞']), # 抽出する品詞の指定
                 UpperCaseFilter()] # アルファベットを大文字に変換
a = Analyzer(token_filters=token_filters)

wb = openpyxl.load_workbook('data\\問合せ管理表サンプル.xlsx')
sheet = wb['QAシート']
row_points = []
with open('data/split_問合せ管理表サンプル.txt', mode="w", encoding='utf_8') as split_out:
    for i in range(103):#Excel何行目まで見るか
        q_cell = sheet['B' + str(i+1)]
        if q_cell.value is not None:
            for token in a.analyze(q_cell.value):
                split_out.write(str(token).split()[0] + ' ')
            split_out.write('\n')


sentences = word2vec.LineSentence('data\\split_問合せ管理表サンプル.txt')
model = word2vec.Word2Vec(sentences,
                          sg=1,         #0: CBOW, 1: skip-gram
                          size=100,     # ベクトルの次元数　大きすぎると複雑な言葉を学習しない、小さすぎると単語の特徴を捉えられない
                          window=5,    # 入力単語からの最大距離
                          min_count=1,  # 単語の出現回数でフィルタリング
                          iter=100,
                          )
model.save('model\\問合せ管理表サンプル.model')
