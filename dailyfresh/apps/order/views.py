from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views import View
from utils.mixin import LoginRequiredMixin
from user.models import Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from django.http import JsonResponse
from datetime import datetime


# Create your views here.
class OrderInfoView(LoginRequiredMixin, View):
    def post(self, request):
        sku_ids = request.POST.getlist("cartList")

        if not all([sku_ids]):
            return redirect(reverse("cart:show"))

        user = request.user
        address = Address.objects.filter(user=user)

        conn = get_redis_connection("default")
        cart_key = "cart_%d" % user.id

        total = 0
        total_price = 0
        goods_li = []
        for sku_id in sku_ids:
            print(sku_id)
            count = int(conn.hget(cart_key, sku_id))
            goods = GoodsSKU.objects.get(id=sku_id)
            total += count
            goods_li.append(goods)
            goods.total_price = count * goods.price
            total_price += goods.total_price
            goods.count = count

        context = {
            "total": total,
            "goods_li": goods_li,
            "total_price": total_price,
            "freight": 10,
            "count_pirce": total_price + 10,
            "address": address,
            "sku_ids": ",".join(sku_ids),
        }
        return render(request, "place_order.html", context)

class OrderCommitView(View):
    def post(self, request):
        user = request.user

        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'type': "err", 'errmsg': '用户未登录'})

        addr_id = request.POST.get("addr")
        payStyle = request.POST.get("payStyle")
        skuIds = request.POST.get("skuIds")
        # 校验参数
        if not all([addr_id, payStyle, skuIds]):
            return JsonResponse({'type': "err", 'errmsg': '参数不完整'})

        # 校验支付方式
        if payStyle not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'type': "err", 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'type': "err", 'errmsg': '地址非法'})

        # todo: 创建订单核心业务

        # 组织参数
        # 订单id: 20171122181630+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # todo: 向df_order_info表中添加一条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                         user=user,
                                         addr=addr,
                                         pay_method=payStyle,
                                         total_count=total_count,
                                         total_price=total_price,
                                         transit_price=transit_price)
        conn = get_redis_connection("default")
        cart_key = "cart_%d" % user.id
        skuIds = skuIds.split(",")
        for sku_id in skuIds:
            print(sku_id)
            # 获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except:
                # 商品不存在
                return JsonResponse({'type': "err", 'errmsg': '商品不存在'})

            count = int(conn.hget(cart_key, sku_id))
            total_count += count
            price = sku.price
            total_price += price * count

            # todo: 向df_order_goods表中添加一条记录
            OrderGoods.objects.create(order=order,
                                      sku=sku,
                                      count=count,
                                      price=price)

            # todo: 更新商品的库存和销量
            sku.stock -= count
            sku.sales += count
            sku.save()

        # todo: 更新订单信息表中的商品的总数量和总价格
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        conn.hdel(cart_key, *skuIds)

        return JsonResponse({'type': "success", 'msg': '成功'})
