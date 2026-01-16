#!/usr/bin/env python3
"""
End-to-End Test for Brand Voice Training Feature

This script tests the complete workflow:
1. Upload 10 example brand content pieces
2. Train brand voice profile and verify metrics
3. Create campaign with trained profile
4. Generate content and verify brand voice consistency (>80%)
5. Export and re-import profile successfully
"""

import json
import sys
import time
from typing import Dict, List, Any
import requests

# Configuration
LANGCHAIN_URL = "http://localhost:8001"
TIMEOUT = 30

# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class E2ETest:
    def __init__(self):
        self.profile_id = None
        self.campaign_id = None
        self.imported_profile_id = None
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def print_step(self, step_num: int, message: str):
        """Print a test step header"""
        print(f"\n{YELLOW}Step {step_num}:{NC} {message}")

    def print_success(self, message: str):
        """Print success message"""
        print(f"{GREEN}✓ {message}{NC}")

    def print_error(self, message: str):
        """Print error message and exit"""
        print(f"{RED}✗ {message}{NC}", file=sys.stderr)
        sys.exit(1)

    def print_info(self, message: str):
        """Print info message"""
        print(f"{BLUE}ℹ {message}{NC}")

    def check_services(self):
        """Verify required services are running"""
        self.print_step(0, "Checking services are running...")

        try:
            response = self.session.get(f"{LANGCHAIN_URL}/health", timeout=5)
            if response.status_code != 200:
                self.print_error(f"LangChain service health check failed: {response.status_code}")
            self.print_success("Services are running")
        except requests.exceptions.RequestException as e:
            self.print_error(f"Cannot connect to LangChain service: {e}")

    def upload_and_train_profile(self):
        """Step 1: Upload 10 example pieces and train profile"""
        self.print_step(1, "Training brand voice profile with 10 example pieces...")

        # Example content representing a tech-savvy, friendly, professional brand
        example_content = [
            "We believe technology should empower people, not replace them. Our AI tools augment human creativity.",
            "Here's how we're revolutionizing marketing: smart automation meets human insight. The result? Better campaigns, faster.",
            "Data-driven decisions are great, but intuition matters too. We help you balance both for optimal results.",
            "Marketing doesn't have to be complicated. Our platform simplifies campaign management while delivering powerful analytics.",
            "Your brand voice is unique. That's why we built tools that learn from your content and amplify what makes you special.",
            "Innovation isn't just about new features. It's about solving real problems in ways that feel natural and intuitive.",
            "We're on a mission to make enterprise-grade marketing tools accessible to teams of all sizes. No complexity, just results.",
            "Behind every great campaign is a team that understands their audience. Our AI helps you connect more authentically.",
            "Time is your most valuable resource. We built our platform to give you more of it by automating the tedious stuff.",
            "Great content tells a story. Our tools help you craft narratives that resonate with your audience and drive action."
        ]

        payload = {
            "profile_name": "Test Brand Voice E2E",
            "example_content": example_content,
            "campaign_id": None
        }

        try:
            response = self.session.post(
                f"{LANGCHAIN_URL}/brand-voice/train",
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            self.profile_id = data.get('id')

            if not self.profile_id:
                self.print_error(f"No profile ID in response: {data}")

            self.print_success(f"Brand voice profile created with ID: {self.profile_id}")
            return data

        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to train profile: {e}")

    def verify_metrics(self):
        """Step 2: Verify brand voice metrics were calculated"""
        self.print_step(2, "Verifying brand voice metrics were calculated...")

        try:
            response = self.session.get(
                f"{LANGCHAIN_URL}/brand-voice/profiles/{self.profile_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Check for calculated_profile
            calculated_profile = data.get('calculated_profile')
            if not calculated_profile:
                self.print_error("Profile missing calculated_profile field")

            # Check for required metrics
            required_metrics = [
                'tone_analysis',
                'readability_metrics',
                'vocabulary_patterns'
            ]

            missing_metrics = []
            for metric in required_metrics:
                if metric not in calculated_profile:
                    missing_metrics.append(metric)

            if missing_metrics:
                self.print_error(f"Missing metrics: {', '.join(missing_metrics)}")

            self.print_success("All brand voice metrics calculated successfully")

            # Display key metrics
            self.print_info("Profile Metrics:")
            if 'tone_analysis' in calculated_profile:
                print(f"  Tone: {json.dumps(calculated_profile['tone_analysis'], indent=2)}")
            if 'readability_metrics' in calculated_profile:
                print(f"  Readability: {json.dumps(calculated_profile['readability_metrics'], indent=2)}")

            return data

        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to get profile: {e}")

    def create_campaign_with_profile(self):
        """Step 3: Create campaign with trained profile assigned"""
        self.print_step(3, "Creating campaign with trained profile assigned...")

        payload = {
            "name": "E2E Test Campaign with Brand Voice",
            "status": "active",
            "target_audience": "B2B marketers",
            "brand_voice_profile_id": self.profile_id
        }

        try:
            response = self.session.post(
                f"{LANGCHAIN_URL}/campaigns",
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            self.campaign_id = data.get('id')

            if not self.campaign_id:
                self.print_error(f"No campaign ID in response: {data}")

            self.print_success(f"Campaign created with ID: {self.campaign_id}")

            # Verify profile is linked
            response = self.session.get(
                f"{LANGCHAIN_URL}/campaigns/{self.campaign_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()

            campaign_data = response.json()
            if campaign_data.get('brand_voice_profile_id') != self.profile_id:
                self.print_error("Campaign not properly linked to brand voice profile")

            self.print_success("Campaign successfully linked to brand voice profile")
            return data

        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to create campaign: {e}")

    def generate_and_verify_content(self):
        """Step 4: Generate content and verify brand voice consistency"""
        self.print_step(4, "Generating content with brand voice profile...")

        payload = {
            "content_type": "linkedin_post",
            "topic": "AI-powered marketing automation",
            "target_audience": "B2B marketers",
            "brand_voice_profile_id": self.profile_id
        }

        try:
            response = self.session.post(
                f"{LANGCHAIN_URL}/agents/content",
                json=payload,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            content = data.get('content', '')

            if not content:
                self.print_error(f"No content generated: {data}")

            self.print_success("Content generated successfully")
            self.print_info("Generated Content Preview:")
            print(f"  {content[:200]}..." if len(content) > 200 else f"  {content}")

            # Check brand voice consistency
            consistency_score = self.calculate_consistency_score(content)

            print(f"\n{BLUE}Brand Voice Consistency Score: {consistency_score}%{NC}")

            if consistency_score >= 80:
                self.print_success(f"Content matches brand voice (score: {consistency_score}% >= 80%)")
            else:
                self.print_error(f"Content does not match brand voice well enough (score: {consistency_score}% < 80%)")

            return data, consistency_score

        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to generate content: {e}")

    def calculate_consistency_score(self, content: str) -> int:
        """Calculate brand voice consistency score based on key indicators"""
        content_lower = content.lower()
        score = 0

        # Check for empowerment/simplification language (25%)
        if any(word in content_lower for word in ['empower', 'augment', 'simplif', 'innovate']):
            score += 25

        # Check for inclusive language (25%)
        if any(word in content_lower for word in ['we', 'our', 'us']):
            score += 25

        # Check for tech/AI focus (25%)
        if any(word in content_lower for word in ['ai', 'automat', 'data', 'technology']):
            score += 25

        # Check for people/audience focus (25%)
        if any(word in content_lower for word in ['team', 'audience', 'people', 'human']):
            score += 25

        return score

    def export_profile(self):
        """Step 5a: Export brand voice profile"""
        self.print_step(5, "Exporting brand voice profile...")

        try:
            response = self.session.get(
                f"{LANGCHAIN_URL}/brand-voice/profiles/{self.profile_id}/export",
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            if 'profile_name' not in data:
                self.print_error(f"Invalid export data: {data}")

            # Save to file
            export_file = f"brand_voice_export_{self.profile_id}.json"
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.print_success(f"Profile exported successfully to {export_file}")
            return data

        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to export profile: {e}")

    def import_profile(self, export_data: Dict[str, Any]):
        """Step 5b: Re-import brand voice profile"""
        self.print_step("5b", "Re-importing brand voice profile...")

        # Modify profile name to avoid conflicts
        import_data = export_data.copy()
        import_data['profile_name'] = "Test Brand Voice E2E (Imported)"

        try:
            response = self.session.post(
                f"{LANGCHAIN_URL}/brand-voice/import",
                json=import_data,
                timeout=TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            self.imported_profile_id = data.get('id')

            if not self.imported_profile_id:
                self.print_error(f"No profile ID in import response: {data}")

            self.print_success(f"Profile re-imported successfully with ID: {self.imported_profile_id}")

            # Verify imported profile has calculated_profile
            response = self.session.get(
                f"{LANGCHAIN_URL}/brand-voice/profiles/{self.imported_profile_id}",
                timeout=TIMEOUT
            )
            response.raise_for_status()

            imported_data = response.json()
            if 'calculated_profile' not in imported_data:
                self.print_error("Imported profile missing calculated_profile")

            self.print_success("Imported profile has all required data")
            return data

        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to import profile: {e}")

    def cleanup(self):
        """Step 6: Clean up test data"""
        self.print_step(6, "Cleaning up test data...")

        # Delete imported profile
        if self.imported_profile_id:
            try:
                self.session.delete(
                    f"{LANGCHAIN_URL}/brand-voice/profiles/{self.imported_profile_id}",
                    timeout=TIMEOUT
                )
                self.print_success("Deleted imported profile")
            except Exception as e:
                print(f"Warning: Could not delete imported profile: {e}")

        # Delete original profile
        if self.profile_id:
            try:
                self.session.delete(
                    f"{LANGCHAIN_URL}/brand-voice/profiles/{self.profile_id}",
                    timeout=TIMEOUT
                )
                self.print_success("Deleted original profile")
            except Exception as e:
                print(f"Warning: Could not delete original profile: {e}")

        # Delete campaign
        if self.campaign_id:
            try:
                self.session.delete(
                    f"{LANGCHAIN_URL}/campaigns/{self.campaign_id}",
                    timeout=TIMEOUT
                )
                self.print_success("Deleted test campaign")
            except Exception as e:
                print(f"Warning: Could not delete campaign: {e}")

    def run(self):
        """Run the complete E2E test"""
        print(f"\n{YELLOW}{'=' * 50}{NC}")
        print(f"{YELLOW}Brand Voice Training E2E Test{NC}")
        print(f"{YELLOW}{'=' * 50}{NC}")

        try:
            # Execute all test steps
            self.check_services()
            self.upload_and_train_profile()
            self.verify_metrics()
            self.create_campaign_with_profile()
            self.generate_and_verify_content()
            export_data = self.export_profile()
            self.import_profile(export_data)
            self.cleanup()

            # Print summary
            print(f"\n{GREEN}{'=' * 50}{NC}")
            print(f"{GREEN}All E2E Tests Passed Successfully!{NC}")
            print(f"{GREEN}{'=' * 50}{NC}\n")

            print("Summary:")
            print("  ✓ Uploaded 10 example brand content pieces")
            print("  ✓ Trained brand voice profile with calculated metrics")
            print("  ✓ Created campaign with trained profile assigned")
            print("  ✓ Generated content matching brand voice (consistency >= 80%)")
            print("  ✓ Exported and re-imported profile successfully")
            print("  ✓ Cleaned up test data")
            print()

            return 0

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Test interrupted by user{NC}")
            self.cleanup()
            return 1
        except Exception as e:
            print(f"\n{RED}Unexpected error: {e}{NC}", file=sys.stderr)
            self.cleanup()
            return 1


if __name__ == "__main__":
    test = E2ETest()
    sys.exit(test.run())
