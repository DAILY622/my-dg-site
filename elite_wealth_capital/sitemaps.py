"""
Django Sitemap Configuration for Elite Wealth Capital
Generates XML sitemaps for search engine crawling
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal


class StaticSitemap(Sitemap):
    """Static pages sitemap - public pages visible to all"""
    
    changefreq = 'weekly'
    priority = 1.0
    protocol = 'https'
    
    def items(self):
        """Return list of static pages"""
        return [
            {
                'name': 'home',
                'priority': 1.0,
                'changefreq': 'daily',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:home',
                'priority': 0.9,
                'changefreq': 'daily',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:about',
                'priority': 0.8,
                'changefreq': 'monthly',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:contact',
                'priority': 0.7,
                'changefreq': 'monthly',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:faq',
                'priority': 0.7,
                'changefreq': 'weekly',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:team',
                'priority': 0.6,
                'changefreq': 'monthly',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:testimonials',
                'priority': 0.6,
                'changefreq': 'weekly',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:news',
                'priority': 0.7,
                'changefreq': 'daily',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:privacy',
                'priority': 0.5,
                'changefreq': 'yearly',
                'lastmod': timezone.now(),
            },
            {
                'name': 'dashboard:terms',
                'priority': 0.5,
                'changefreq': 'yearly',
                'lastmod': timezone.now(),
            },
        ]
    
    def location(self, item):
        """Get URL from item"""
        try:
            return reverse(item['name'])
        except:
            return '/'
    
    def lastmod(self, item):
        """Get last modification time"""
        return item.get('lastmod')
    
    def changefreq(self, item):
        """Get change frequency"""
        return item.get('changefreq', 'weekly')
    
    def priority(self, item):
        """Get priority"""
        return item.get('priority', 0.5)


class InvestmentPlanSitemap(Sitemap):
    """Investment plans sitemap"""
    
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'
    
    def items(self):
        """Return all active investment plans"""
        try:
            from investments.models import InvestmentPlan
            return InvestmentPlan.objects.filter(
                is_active=True
            ).order_by('-created_at')
        except:
            return []
    
    def location(self, obj):
        """Get plan URL"""
        return f'/investments/plans/{obj.id}/'
    
    def lastmod(self, obj):
        """Get last modification"""
        return obj.updated_at if hasattr(obj, 'updated_at') else None
    
    def priority(self, obj):
        """Higher priority for popular plans"""
        if hasattr(obj, 'popularity_score'):
            return min(0.9, 0.5 + (obj.popularity_score / 100))
        return 0.7


class NewsArticleSitemap(Sitemap):
    """News and blog articles sitemap"""
    
    changefreq = 'weekly'
    priority = 0.6
    protocol = 'https'
    
    def items(self):
        """Return recent news articles"""
        # This would need a News model
        # For now, returning empty list
        return []
    
    def location(self, obj):
        """Get article URL"""
        return f'/dashboard/news/{obj.id}/'
    
    def lastmod(self, obj):
        """Get publication date"""
        return obj.published_at if hasattr(obj, 'published_at') else None


class CategorySitemap(Sitemap):
    """Investment categories sitemap"""
    
    changefreq = 'monthly'
    priority = 0.7
    protocol = 'https'
    
    def items(self):
        """Return investment categories"""
        try:
            from investments.models import InvestmentPlan
            # Get unique categories from plans
            plans = InvestmentPlan.objects.filter(
                is_active=True
            ).values_list('category', flat=True).distinct()
            
            return [{'id': cat, 'name': cat} for cat in plans if cat]
        except:
            return []
    
    def location(self, obj):
        """Get category URL"""
        return f'/investments/category/{obj["id"]}/'
    
    def priority(self, obj):
        """All categories same priority"""
        return 0.7


class MobileAppSitemap(Sitemap):
    """Mobile app related pages"""
    
    changefreq = 'monthly'
    priority = 0.6
    protocol = 'https'
    
    def items(self):
        """Return mobile app pages"""
        return [
            {
                'name': 'dashboard:install_app',
                'priority': 0.7,
                'changefreq': 'monthly',
            },
        ]
    
    def location(self, item):
        """Get URL"""
        try:
            return reverse(item['name'])
        except:
            return '/'


class LegalSitemap(Sitemap):
    """Legal and compliance pages"""
    
    changefreq = 'yearly'
    priority = 0.4
    protocol = 'https'
    
    def items(self):
        """Return legal pages"""
        return [
            {
                'name': 'dashboard:privacy',
                'priority': 0.5,
            },
            {
                'name': 'dashboard:terms',
                'priority': 0.5,
            },
            {
                'name': 'dashboard:contact',
                'priority': 0.4,
            },
        ]
    
    def location(self, item):
        """Get URL"""
        try:
            return reverse(item['name'])
        except:
            return '/'


# Sitemap index mapping
sitemaps = {
    'static': StaticSitemap,
    'plans': InvestmentPlanSitemap,
    'news': NewsArticleSitemap,
    'categories': CategorySitemap,
    'mobile': MobileAppSitemap,
    'legal': LegalSitemap,
}
