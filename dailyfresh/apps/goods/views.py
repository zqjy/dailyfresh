from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views import View
from django.core.cache import cache
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from django_redis import get_redis_connection
from order.models import OrderGoods
from django.core.paginator import Paginator


# Create your views here.
class IndexView(View):
    """
    首页视图类
    """

    def get(self, request):
        # 尝试从缓存中获取数据
        context = cache.get("page_index_data")
        cache.delete("page_index_data")
        if context is None:
            print("设置缓存")
            # 获取商品分类
            types = GoodsType.objects.all()
            # 获取商品轮播图
            goods_banners = IndexGoodsBanner.objects.all().order_by("index")
            # 获取活动
            promotion_banners = IndexPromotionBanner.objects.all().order_by("index")
            # 获取各分类商品
            for type in types:
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by("index")
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by("index")
                type.title_banners = title_banners
                type.image_banners = image_banners
                for a in image_banners:
                    print(a.sku.id, a.sku.name)
            context = {
                "types": types,
                "goods_banners": goods_banners,
                "promotion_banners": promotion_banners,
            }
            cache.set("page_index_data", context, 3600)
        # 获取购物车数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


# /goods/id
class DetailView(View):
    """商品详细页面"""

    def get(self, request, goods_id):
        types = GoodsType.objects.all()

        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse("goods:index"))

        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by("-create_time")[:2]

        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        user = request.user

        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)

            conn = get_redis_connection("default")
            history_key = "history_%d" % user.id
            conn.lrem(history_key, 0, sku.id)
            conn.lpush(history_key, sku.id)
            conn.ltrim(history_key, 0, 4)

        context = {
            "types": types,
            "sku": sku,
            "same_spu_skus": same_spu_skus,
            "new_skus": new_skus,
            "sku_orders": sku_orders,
            "cart_count": cart_count,
        }
        return render(request, "detail.html", context)


class ListView(View):
    """
    商品列表页
    """

    def get(self, request, type_id, page):
        types = GoodsType.objects.all()
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            redirect(reverse("goods:index"))

        new_skus = GoodsSKU.objects.filter(type=type).order_by("-create_time")[0:2]

        sort = request.GET.get("sort")

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        paginator = Paginator(skus, 1)

        try:
            page = int(page)
        except:
            page = 1

        max_page = paginator.num_pages
        if page > max_page:
            page = 1

        skus_page = paginator.page(page)

        # 自定义页码显示的数量
        if page <= 3:
            if max_page >= 5:
                pages = range(1, 6)
            else:
                pages = range(1, max_page + 1)
        elif page > max_page - 2:
            if max_page >= 5:
                pages = range(max_page - 4, max_page + 1)
            else:
                pages = range(1, max_page + 1)
        else:
            if page + 3 <= max_page:
                pages = range(page - 2, page + 3)
            else:
                pages = range(page - 2, max_page + 1)

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)

        context = {
            "types": types,
            "type": type,
            "cart_count": cart_count,
            "new_skus": new_skus,
            "skus_page": skus_page,
            "sort": sort,
            "pages": pages,
        }
        return render(request, "list.html", context)
