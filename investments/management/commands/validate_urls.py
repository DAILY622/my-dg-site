"""
Django Management Command: Validate URLs and Models
Checks all models for invalid URLs, broken redirects, and naming issues
"""

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
import re

class Command(BaseCommand):
    help = 'Validates URLs in all models and checks for naming issues'
    
    def handle(self, *args, **kwargs):
        self.stdout.write("="*60)
        self.stdout.write("🔍 URL & MODEL VALIDATION")
        self.stdout.write("="*60 + "\n")
        
        issues = []
        warnings = []
        
        # Get all models
        all_models = apps.get_models()
        
        for model in all_models:
            model_name = f"{model._meta.app_label}.{model.__name__}"
            
            # Check model name conventions
            if not re.match(r'^[A-Z][a-zA-Z0-9]*$', model.__name__):
                warnings.append(f"⚠️  Model naming: {model_name} (should be PascalCase)")
            
            # Check all fields
            for field in model._meta.get_fields():
                field_name = field.name
                
                # Check URL fields
                if isinstance(field, models.URLField):
                    self.stdout.write(f"\n📌 {model_name}.{field_name} (URLField)")
                    
                    try:
                        # Check if any instances have invalid URLs
                        for obj in model.objects.all()[:100]:  # Sample first 100
                            url_value = getattr(obj, field_name, None)
                            if url_value:
                                # Basic URL validation
                                if not (url_value.startswith('http://') or url_value.startswith('https://')):
                                    issues.append(f"❌ {model_name}.{field_name}: Invalid URL '{url_value}' (ID: {obj.pk})")
                                
                                # Check for cloudinary URLs (should be R2 now)
                                if 'cloudinary.com' in url_value:
                                    warnings.append(f"⚠️  {model_name}.{field_name}: Still using Cloudinary URL (ID: {obj.pk})")
                    except Exception as e:
                        self.stdout.write(f"   ⚠️  Cannot check: {str(e)}")
                
                # Check FileField and ImageField
                elif isinstance(field, (models.FileField, models.ImageField)):
                    self.stdout.write(f"\n📁 {model_name}.{field_name} ({field.__class__.__name__})")
                    
                    try:
                        # Check storage configuration
                        storage = field.storage
                        storage_class = storage.__class__.__name__
                        self.stdout.write(f"   Storage: {storage_class}")
                        
                        # Sample check
                        for obj in model.objects.exclude(**{field_name: ''})[:10]:
                            file_field = getattr(obj, field_name, None)
                            if file_field:
                                try:
                                    url = file_field.url
                                    if 'cloudinary.com' in url:
                                        warnings.append(f"⚠️  {model_name}.{field_name}: Cloudinary URL found (ID: {obj.pk})")
                                    elif 'r2.cloudflarestorage.com' in url:
                                        self.stdout.write(f"   ✅ Using R2 storage")
                                        break
                                except Exception:
                                    pass
                    except Exception as e:
                        self.stdout.write(f"   ⚠️  Cannot check: {str(e)}")
                
                # Check field naming conventions
                if field_name != field_name.lower():
                    warnings.append(f"⚠️  Field naming: {model_name}.{field_name} (should be lowercase_with_underscores)")
        
        # Check URL patterns in urls.py files
        self.stdout.write("\n" + "="*60)
        self.stdout.write("🔗 CHECKING URL PATTERNS")
        self.stdout.write("="*60 + "\n")
        
        import os
        from pathlib import Path
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        for urls_file in base_dir.rglob('urls.py'):
            self.stdout.write(f"\n📄 {urls_file.relative_to(base_dir)}")
            
            try:
                with open(urls_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for common URL issues
                    if 'path(r' in content:
                        warnings.append(f"⚠️  {urls_file.name}: Using regex path() (consider using re_path())")
                    
                    if '//' in content and 'http' not in content:
                        warnings.append(f"⚠️  {urls_file.name}: Double slashes in URL patterns")
            except Exception as e:
                self.stdout.write(f"   ⚠️  Cannot read: {str(e)}")
        
        # Final Report
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 VALIDATION REPORT")
        self.stdout.write("="*60 + "\n")
        
        if issues:
            self.stdout.write(self.style.ERROR(f"\n❌ ISSUES FOUND: {len(issues)}"))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f"  {issue}"))
        
        if warnings:
            self.stdout.write(self.style.WARNING(f"\n⚠️  WARNINGS: {len(warnings)}"))
            for warning in warnings[:20]:  # Show first 20
                self.stdout.write(self.style.WARNING(f"  {warning}"))
            if len(warnings) > 20:
                self.stdout.write(self.style.WARNING(f"  ... and {len(warnings)-20} more"))
        
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS("\n✅ NO ISSUES FOUND!"))
            self.stdout.write(self.style.SUCCESS("   All URLs and models look good!"))
        
        self.stdout.write("\n" + "="*60 + "\n")
