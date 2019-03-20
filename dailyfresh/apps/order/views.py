from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views import View
from django.db import transaction
from django.conf import settings
from utils.mixin import LoginRequiredMixin
from user.models import Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from django.http import JsonResponse
from datetime import datetime
from alipay import AliPay
import os


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


class OrderCommitView1(View):
    @transaction.atomic
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
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        order_point = transaction.savepoint()
        try:
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
                # 获取商品的信息
                try:
                    # sku = GoodsSKU.objects.get(id=sku_id)
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    # 商品不存在
                    transaction.savepoint_rollback(order_point)
                    return JsonResponse({'type': "err", 'errmsg': '商品不存在'})

                count = int(conn.hget(cart_key, sku_id))
                total_count += count
                price = sku.price
                total_price += price * count

                if count > sku.stock:
                    transaction.savepoint_rollback(order_point)
                    return JsonResponse({'type': "err", 'errmsg': '商品库存不足'})

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
        except Exception as e:
            print(e)
            transaction.savepoint_rollback(order_point)
            return JsonResponse({'type': "err", 'errmsg': '下单失败'})

        transaction.savepoint_commit(order_point)

        conn.hdel(cart_key, *skuIds)

        return JsonResponse({'type': "success", 'msg': '成功'})


class OrderCommitView(View):
    @transaction.atomic
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
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        order_point = transaction.savepoint()
        try:
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
                for i in range(3):
                    # 获取商品的信息
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                        # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    except:
                        # 商品不存在
                        transaction.savepoint_rollback(order_point)
                        return JsonResponse({'type': "err", 'errmsg': '商品不存在'})

                    count = int(conn.hget(cart_key, sku_id))
                    total_count += count
                    price = sku.price
                    total_price += price * count

                    if count > sku.stock:
                        transaction.savepoint_rollback(order_point)
                        return JsonResponse({'type': "err", 'errmsg': '商品库存不足'})

                    new_stock = sku.stock - count
                    new_sales = sku.sales + count
                    # todo: 更新商品的库存和销量
                    ret_num = GoodsSKU.objects.filter(id=sku_id, stock=sku.stock).update(stock=new_stock,
                                                                                         sales=new_sales)
                    if ret_num == 0:
                        if i == 2:
                            transaction.savepoint_rollback(order_point)
                            return JsonResponse({'type': "err", 'errmsg': '下单失败'})
                        continue

                    # todo: 向df_order_goods表中添加一条记录
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=price)

                    # # todo: 更新商品的库存和销量
                    # sku.stock -= count
                    # sku.sales += count
                    # sku.save()
                    break

            # todo: 更新订单信息表中的商品的总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            print("err: ", e)
            transaction.savepoint_rollback(order_point)
            return JsonResponse({'type': "err", 'errmsg': '下单失败'})

        transaction.savepoint_commit(order_point)

        conn.hdel(cart_key, *skuIds)

        return JsonResponse({'type': "success", 'msg': '成功'})


class PayOrderView(View):
    def post(self, request):
        '''订单支付'''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'type': 'err', 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'type': 'err', 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'type': 'err', 'errmsg': '订单错误'})

        # 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid="2016092700604429",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'type': "success", 'pay_url': pay_url})


class CheckPayView(View):
    def post(self, request):
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"type": "err", "errmsg": "请登录"})

        # 接受参数订单ID
        order_id = request.POST.get("order_id")

        try:
            order = OrderInfo.objects.get(order_id=order_id, pay_method=3, order_status=1, user=user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({"type": "err", "errmsg": "订单错误"})

        alipay = getAliPay()

        while True:
            resp = alipay.api_alipay_trade_query(order_id)
            # dict = {'receipt_amount': '0.00',
            #         'invoice_amount': '0.00',
            #         'trade_status': 'TRADE_SUCCESS',
            #         'total_amount': '64.24',
            #         'send_pay_date': '2019-03-19 16:21:20',
            #         'point_amount': '0.00',
            #         'out_trade_no': '2019031913432222',
            #         'msg': 'Success',
            #         'code': '10000',
            #         'buyer_logon_id': 'sax***@sandbox.com',
            #         'buyer_user_id': '2088102177769471',
            #         'trade_no': '2019031922001469471000421484',
            #         'buyer_pay_amount': '0.00',
            #         'buyer_user_type': 'PRIVATE'}

            code = resp.get("code")
            trade_status = resp.get("trade_status")

            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = resp.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4
                order.save()
                return JsonResponse({"type": "success", "msg": "付款成功"})
            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                import time
                time.sleep(5)
                continue
            else:
                print(code)
                return JsonResponse({"type": "success", "msg": "付款失败, err:%s" % code})


class CommentView(LoginRequiredMixin, View):
    def get(self, request, order_id):

        if not order_id:
            return redirect(reverse("user:order", kwargs={'page': 1}))

        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id, order_status=4, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order", kwargs={'page': 1}))

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        context = {"order": order}

        return render(request, "order_comment.html", context)

    def post(self, request, order_id):
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order', kwargs={'page': 1}))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order", kwargs={'page': 1}))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))



def getAliPay():
    # 业务处理:使用python sdk调用支付宝的支付接口
    # 初始化
    alipay = AliPay(
        appid="2016092700604429",  # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
        alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    return alipay
