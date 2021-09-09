$(function(){
    var botui = new BotUI('chatbot');
    // 初期メッセージ
    botui.message.add({
        content: 'こんにちは。chatbotです。'
    }).then(question());
    
    // 質問開始
    function question() {
        botui.message.add({
          delay:1000,
          content: '質問を入力してください。'
        }).then(function() {
            return botui.action.text({
                delay:1000,
                action: {
                    placeholder: '質問を入力...'
                }
            }).then(function(res) {
                var answer;
                $.ajax("/question", {
                    type: "post",
                    data: {"question":res.value},  // 質問
                    dataType: "json",
                }).done(function(data) { // 通信成功
                    console.log("Ajax通信 成功");
                    information = JSON.parse(data.values).information
                    hit_question = JSON.parse(data.values).hit_question
                    hit_answer = JSON.parse(data.values).hit_answer
                    botui.message.add({
                        delay:1000,
                        type: "html",
                        content: `${information}<br>
                            質問：<br>
                            <b>${hit_question}</b><br>
                            回答：<br>
                            <b>${hit_answer}</b>
                            `
                    })
                }).fail(function(data) {
                    console.log("Ajax通信 失敗");// 通信失敗
                    return botui.message.add({
                        delay:1000,
                        type: "html",
                        content: `<b>すみません。通信に失敗しました。</b>`
                    })
                }).always(function(){
                    askEnd()
                })
            })
        })
      }
    
    // プログラムを終了するか聞く関数
    function askEnd(){
        botui.message.add({
        delay:1500,
        content: '他に質問がありますか？'
        }).then(function() {

        // ボタンを提示する．
        return botui.action.button({
            delay: 1500,
            action: [
            {icon: 'circle-o', text: 'はい', value: true},
            {icon: 'close', text: 'いいえ', value: false}]
        });
        }).then(function(res) {
        res.value ? question() : end();
        });
    }

    //プログラムを終了する関数
    function end() {
        botui.message.add({
        delay: 1500,
        content: 'ご利用ありがとうございました。'
        });
    }

});