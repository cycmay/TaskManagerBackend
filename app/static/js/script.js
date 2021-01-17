$('#select_name_add').select2({
    ajax: {
        url: "{{ url_for('api_v1.api_duproducts') }}",
        dataType: 'json',
        delay: 250,
        data: function (params) {
            console.log("macc");
            return {
                // params.term表示输入框中内容，q发生到服务器的参数名
                keyword: params.term
            }
        },
        processResults: function (data) {
            // 构造select信息
            for (i in ret.products) {
                var options = [];
                content = '<img src='.ret.products[i]['logoUrl'] + 'width="50" style="margin-right:5px">'.ret.products[i]['sellDate'] +
                    ' ['.ret.products[i]['articleNumber'] +
                    '] '.ret.products[i]['title'];
                options.push(content);
            }
            return {
                results: options
            };
        },
        cache: true,
        escapeMarkup: function (markup) {
            return markup;
        },
        minimumInputLength: 1
    }
});