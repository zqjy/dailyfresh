from django.contrib import admin
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from django.core.cache import cache


class BaseModuleAdmin(admin.ModelAdmin):
    """
    模型管理基础类
    """

    def save_model(self, request, obj, form, change):
        """模型保存时调用"""
        super().save_model(request, obj, form, change)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        cache.delete("page_index_data")

    def delete_model(self, request, obj):
        """模型删除时调用"""
        super().delete_model(request, obj)

        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        cache.delete("page_index_data")


class GoodsTypeModuleAdmin(BaseModuleAdmin):
    pass


class IndexGoodsBannerModuleAdmin(BaseModuleAdmin):
    pass


class IndexPromotionBannerModuleAdmin(BaseModuleAdmin):
    pass


class IndexTypeGoodsBannerModuleAdmin(BaseModuleAdmin):
    pass


class GoodsSKUModuleAdmin(BaseModuleAdmin):
    pass


# Register your models here.
admin.site.register(GoodsType, GoodsTypeModuleAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerModuleAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerModuleAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerModuleAdmin)
admin.site.register(GoodsSKU, GoodsSKUModuleAdmin)
