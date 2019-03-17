from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

# Create your views here.
# /cart/add
class AddCartView(View):
    def post(self, request):
        ret_json = {}
        user = request.user

        ret_json["type"] = "err"
        ret_json["errmsg"] = ""
        if not ret_json["errmsg"] and not user.is_authenticated():
            ret_json["errmsg"] = "请登入"

        num = request.POST.get("num")
        skuid = request.POST.get("skuid")

        if not ret_json["errmsg"] and not all([num, skuid]):
            ret_json["errmsg"] = "数据不完整"

        try:
            num = int(num)
        except Exception:
            ret_json["errmsg"] = "参数格式不正确"

        try:
            goods = GoodsSKU.objects.get(id=skuid)
        except GoodsSKU.DoesNotExist:
            ret_json["errmsg"] = "id: %s, 没有对应商品" % skuid

        conn = get_redis_connection("default")

        cart_key = "cart_%d" % user.id

        count = conn.hget(cart_key, skuid)
        if count:
            num += int(count)

        if not ret_json["errmsg"] and num > goods.stock:
            ret_json["errmsg"] = "库存不足"

        if not ret_json["errmsg"]:
            conn.hset(cart_key, skuid, num)
            total_count = conn.hlen(cart_key)
            ret_json["type"] = "success"
            ret_json["total_count"] = total_count
            ret_json["msg"] = "成功"

        return JsonResponse(ret_json)

# /cart
class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        cart_key = "cart_%d" % user.id

        conn = get_redis_connection("default")
        cart_dict = conn.hgetall(cart_key)

        total = 0
        total_price = 0
        goods_li = []
        for sku_id, count in cart_dict.items():
            count = int(count)
            goods = GoodsSKU.objects.get(id = sku_id)
            total += count
            goods_li.append(goods)
            goods.total_price = count * goods.price
            total_price += goods.total_price
            goods.count = count

        context = {
            "total": total,
            "goods_li": goods_li,
            "total_price": total_price,
        }
        return render(request, "cart.html", context)

