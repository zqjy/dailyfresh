$(document).ready(function () {
    $("input[type=checkbox]").on("change", function () {
        var name = $(this).prop("name");

        if (name == "cartList") {
            var $cartList = $(".cart_list_td");
            var checkbokLength = $cartList.find("input[name=cartList]").length;
            var checkedLeghth = $cartList.find("input[name=cartList]:checked").length;
            if (checkbokLength != checkedLeghth) $("[name=all]").removeAttr("checked");
            else $("[name=all]").prop("checked", "checked");
        } else if (name == "all") {
            if (!$(this).prop("checked")) $("input[name=cartList]:checked").removeAttr("checked");
            else $("input[name=cartList]").prop("checked", "checked");
        }

        updateTotalPrice();
    });

    $(".num_add").on("click", "a", function() {
        var $parent = $(this).parent();
        var $numShow = $parent.find(".num_show");
        if ($(this).hasClass("add")) {
            var num = parseInt($numShow.val())+1;
            var id = $parent.attr("skuid");
            $numShow.val(num);
            commit(id, num, $parent.attr("to"), $numShow);
        } else if($(this).hasClass("minus")) {
            var num = parseInt($numShow.val());
            var id = $parent.attr("skuid");
            if (num>1) num = num-1;
            $numShow.val(num);
            commit(id, num, $parent.attr("to"), $numShow);
        }
    });

    var oldNum = 0;
    $(".num_add").on("focus", "input", function() {
        if ($(this).hasClass("num_show")) {
            oldNum = $(this).val();
        }
    });
    $(".num_add").on("blur", "input", function() {
        var $parent = $(this).parent();
        var $numShow = $parent.find(".num_show");
        if ($(this).hasClass("num_show")) {
            var id = $parent.attr("skuid");
            var num = $(this).val();
            num = parseInt(num);
            if (isNaN(num) || num < 1) num = oldNum;
            $parent.find(".num_show").val(num);
            commit(id, num, $parent.attr("to"), $numShow);
        }

    });

    $("[name=del]").click(function() {
        var id = $(this).attr("skuid");
        var to = $(this).attr("to");
        commit(id, 0, to, $(this).parents("ul"));
    });

});

/**
 * 修改商品总价显示
 */
function updateTotalPrice() {
    var pirce = 0;
    var count = 0;
    var total_count = 0;
    $("input[name=cartList]").each(function(){
         var goods_count = parseInt($(this).parents("ul").find(".num_show").val());
         var goods_price = parseFloat($(this).parents("ul").find(".col05").text());
         $(this).parents("ul").find(".col07").text((goods_price*goods_count).toFixed(2)+"元");
         if (isNaN(goods_count) || goods_count<0) goods_count = 0;
         total_count += goods_count;
    });
    $("input[name=cartList]:checked").each(function(){

        var goods_price = parseFloat($(this).parents("ul").find(".col07").text());
        var goods_count = parseInt($(this).parents("ul").find(".num_show").val());
        if (isNaN(goods_price) || goods_price<0) goods_price = 0;
        if (isNaN(goods_count) || goods_count<0) goods_count = 0;
        pirce += goods_price;
        count += goods_count;
    });

    $(".settlements").find("em").html(pirce.toFixed(2));
    $(".settlements").find("b").html(count);
    $(".total_count em").html(total_count);

}

/**
 * 商品提交
 */
function commit(id, num, to, $this) {
    var csrf = $("input[name=csrfmiddlewaretoken]").val();
    jData = {
        "skuid": id,
        "num": num,
        "csrfmiddlewaretoken": csrf
    }
    $.ajaxSettings.async = false;
    $.post(to, jData, function(json) {
        type = json["type"];
        if (type == "err") {
            msg = json["errmsg"];
            alert("错误信息：" + msg);
        } else if (type == "success"){
            $this.val(json["num"]);
            updateTotalPrice();
        } else if (type == "del") {
            $this.remove();
            updateTotalPrice();
        }
    }, "json");

    $.ajaxSettings.async = true;
}

/**
 * 获取要购买的商品id
 * @returns {string}
 */
function getGoodsIds() {
    var ids = [];
    $("[name=cartList]:checked").each(function () {
        ids.append($(this).attr("skuid"));
    });
    var strIds = ids.join(",");
    return strIds
}