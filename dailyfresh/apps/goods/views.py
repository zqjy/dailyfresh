from django.shortcuts import render
from django.views import View
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


# Create your views here.
class IndexView(View):
    """
    首页视图类
    """
    def get(self, request):
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
        # 获取购物车数量
        cart_count = 0

        context = {
            "types": types,
            "goods_banners": goods_banners,
            "promotion_banners": promotion_banners,
            "cart_count": cart_count,
        }

        return render(request, 'index.html', context)
