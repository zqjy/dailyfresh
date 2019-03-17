$(document).ready(function () {
    var price = $(".show_pirze em").text();
    var num = $(".num_show").val();
    price = parseFloat(price);
    num = parseInt(num);

    countTotal(price, num); // 计算总价

    // 按钮改变商品数量
    $(".num_add").on("click", "a", function(){

        if ($(this).hasClass("add")) num += 1;
        else if ($(this).hasClass("minus")) if (num>1) num -= 1;

        $(".num_show").val(num);
        countTotal(price, num); //计算商品总价
    });

    $(".num_add").on("blur", "input", function(){

        if ($(this).hasClass("num_show")) {
            num = $(this).val();
            num = parseFloat(num);

            if (isNaN(num)) num = 1;
            else num = Math.round(num);

            $(this).val(num);
        }

        countTotal(price, num); //计算商品总价
    });
});

/**
 * 计算商品总价
 * @param price 商品单价
 * @param num 商品数量
 */
function countTotal(price, num) {
    var total = price * num;
    total = total.toFixed(2);

    $(".total em").text(total);
}