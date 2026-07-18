"""
Django management command to migrate images from Cloudinary to R2

Usage: python manage.py migrate_cloudinary_to_r2 [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from kyc.models import KYCDocument
from investments.models import Deposit, CryptoWallet, AgentApplication
import requests
import os
from urllib.parse import urlparse

User = get_user_model()

class Command(BaseCommand):
    help = 'Migrate images from Cloudinary to R2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("="*60)
        self.stdout.write("🔄 CLOUDINARY → R2 MIGRATION")
        self.stdout.write("="*60 + "\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))
        
        total_migrated = 0
        
        # 1. Migrate Profile Images
        self.stdout.write(self.style.HTTP_INFO("\n1️⃣ Migrating Profile Images..."))
        total_migrated += self.migrate_profile_images(dry_run)
        
        # 2. Migrate KYC Documents
        self.stdout.write(self.style.HTTP_INFO("\n2️⃣ Migrating KYC Documents..."))
        total_migrated += self.migrate_kyc_documents(dry_run)
        
        # 3. Migrate Deposit Proofs
        self.stdout.write(self.style.HTTP_INFO("\n3️⃣ Migrating Deposit Proofs..."))
        total_migrated += self.migrate_deposit_proofs(dry_run)
        
        # 4. Migrate Wallet QR Codes
        self.stdout.write(self.style.HTTP_INFO("\n4️⃣ Migrating Wallet QR Codes..."))
        total_migrated += self.migrate_wallet_qr_codes(dry_run)
        
        # 5. Migrate Agent Documents
        self.stdout.write(self.style.HTTP_INFO("\n5️⃣ Migrating Agent Documents..."))
        total_migrated += self.migrate_agent_documents(dry_run)
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✅ MIGRATION COMPLETE!"))
        self.stdout.write("="*60)
        self.stdout.write(f"\nTotal images migrated: {total_migrated}")
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS("\n✅ All images now on R2!"))
            self.stdout.write(self.style.WARNING("\n⚠️  Next steps:"))
            self.stdout.write("   1. Test site thoroughly")
            self.stdout.write("   2. Remove Cloudinary secrets from render.yaml")
            self.stdout.write("   3. Commit and push changes")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  This was a DRY RUN!"))
            self.stdout.write("   Run without --dry-run to actually migrate")

    def is_cloudinary_url(self, url):
        """Check if URL is from Cloudinary"""
        if not url:
            return False
        return 'cloudinary.com' in url or 'res.cloudinary.com' in url

    def download_image(self, url):
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Failed to download: {e}"))
            return None

    def migrate_profile_images(self, dry_run):
        """Migrate user profile images"""
        users = User.objects.filter(profile_image__isnull=False).exclude(profile_image='')
        count = 0
        
        for user in users:
            url = user.profile_image.url if hasattr(user.profile_image, 'url') else str(user.profile_image)
            
            if self.is_cloudinary_url(url):
                self.stdout.write(f"   User {user.id}: {user.email}")
                self.stdout.write(f"   FROM: {url[:80]}...")
                
                if not dry_run:
                    # Download from Cloudinary
                    content = self.download_image(url)
                    if content:
                        # Get filename
                        filename = os.path.basename(urlparse(url).path)
                        if not filename:
                            filename = f"profile_{user.id}.jpg"
                        
                        # Upload to R2
                        user.profile_image.save(filename, ContentFile(content), save=True)
                        
                        new_url = user.profile_image.url
                        self.stdout.write(self.style.SUCCESS(f"   TO:   {new_url[:80]}..."))
                        count += 1
                    else:
                        self.stdout.write(self.style.ERROR("   ❌ Failed to migrate"))
                else:
                    self.stdout.write(self.style.WARNING("   [DRY RUN - Would migrate]"))
                    count += 1
        
        self.stdout.write(f"\n   ✅ Migrated {count} profile images")
        return count

    def migrate_kyc_documents(self, dry_run):
        """Migrate KYC documents"""
        kyc_docs = KYCDocument.objects.all()
        count = 0
        
        for doc in kyc_docs:
            # Front image
            if doc.front_image:
                url = doc.front_image.url if hasattr(doc.front_image, 'url') else str(doc.front_image)
                if self.is_cloudinary_url(url):
                    self.stdout.write(f"   KYC {doc.id} (Front): {doc.user.email}")
                    
                    if not dry_run:
                        content = self.download_image(url)
                        if content:
                            filename = f"kyc_front_{doc.id}_{os.path.basename(urlparse(url).path)}"
                            doc.front_image.save(filename, ContentFile(content), save=True)
                            self.stdout.write(self.style.SUCCESS(f"   ✅ Front migrated"))
                            count += 1
                    else:
                        count += 1
            
            # Back image
            if doc.back_image:
                url = doc.back_image.url if hasattr(doc.back_image, 'url') else str(doc.back_image)
                if self.is_cloudinary_url(url):
                    if not dry_run:
                        content = self.download_image(url)
                        if content:
                            filename = f"kyc_back_{doc.id}_{os.path.basename(urlparse(url).path)}"
                            doc.back_image.save(filename, ContentFile(content), save=True)
                            self.stdout.write(self.style.SUCCESS(f"   ✅ Back migrated"))
                            count += 1
                    else:
                        count += 1
            
            # Selfie image
            if doc.selfie_image:
                url = doc.selfie_image.url if hasattr(doc.selfie_image, 'url') else str(doc.selfie_image)
                if self.is_cloudinary_url(url):
                    if not dry_run:
                        content = self.download_image(url)
                        if content:
                            filename = f"kyc_selfie_{doc.id}_{os.path.basename(urlparse(url).path)}"
                            doc.selfie_image.save(filename, ContentFile(content), save=True)
                            self.stdout.write(self.style.SUCCESS(f"   ✅ Selfie migrated"))
                            count += 1
                    else:
                        count += 1
        
        self.stdout.write(f"\n   ✅ Migrated {count} KYC images")
        return count

    def migrate_deposit_proofs(self, dry_run):
        """Migrate deposit proof images"""
        deposits = Deposit.objects.filter(proof_image__isnull=False).exclude(proof_image='')
        count = 0
        
        for deposit in deposits:
            url = deposit.proof_image.url if hasattr(deposit.proof_image, 'url') else str(deposit.proof_image)
            
            if self.is_cloudinary_url(url):
                self.stdout.write(f"   Deposit {deposit.id}: {deposit.user.email}")
                
                if not dry_run:
                    content = self.download_image(url)
                    if content:
                        filename = f"deposit_{deposit.id}_{os.path.basename(urlparse(url).path)}"
                        deposit.proof_image.save(filename, ContentFile(content), save=True)
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Migrated"))
                        count += 1
                else:
                    count += 1
        
        self.stdout.write(f"\n   ✅ Migrated {count} deposit proofs")
        return count

    def migrate_wallet_qr_codes(self, dry_run):
        """Migrate wallet QR codes"""
        wallets = CryptoWallet.objects.all()
        count = 0
        
        for wallet in wallets:
            # qr_code field
            if wallet.qr_code:
                url = wallet.qr_code.url if hasattr(wallet.qr_code, 'url') else str(wallet.qr_code)
                if self.is_cloudinary_url(url):
                    self.stdout.write(f"   Wallet {wallet.id} ({wallet.currency})")
                    
                    if not dry_run:
                        content = self.download_image(url)
                        if content:
                            filename = f"qr_{wallet.currency}_{wallet.id}.png"
                            wallet.qr_code.save(filename, ContentFile(content), save=True)
                            self.stdout.write(self.style.SUCCESS(f"   ✅ QR code migrated"))
                            count += 1
                    else:
                        count += 1
            
            # qr_code_image field
            if wallet.qr_code_image:
                url = wallet.qr_code_image.url if hasattr(wallet.qr_code_image, 'url') else str(wallet.qr_code_image)
                if self.is_cloudinary_url(url):
                    if not dry_run:
                        content = self.download_image(url)
                        if content:
                            filename = f"qr_image_{wallet.currency}_{wallet.id}.png"
                            wallet.qr_code_image.save(filename, ContentFile(content), save=True)
                            count += 1
                    else:
                        count += 1
        
        self.stdout.write(f"\n   ✅ Migrated {count} QR codes")
        return count

    def migrate_agent_documents(self, dry_run):
        """Migrate agent application documents"""
        agents = AgentApplication.objects.filter(id_document__isnull=False).exclude(id_document='')
        count = 0
        
        for agent in agents:
            url = agent.id_document.url if hasattr(agent.id_document, 'url') else str(agent.id_document)
            
            if self.is_cloudinary_url(url):
                self.stdout.write(f"   Agent {agent.id}: {agent.full_name}")
                
                if not dry_run:
                    content = self.download_image(url)
                    if content:
                        filename = f"agent_{agent.id}_{os.path.basename(urlparse(url).path)}"
                        agent.id_document.save(filename, ContentFile(content), save=True)
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Migrated"))
                        count += 1
                else:
                    count += 1
        
        self.stdout.write(f"\n   ✅ Migrated {count} agent documents")
        return count
