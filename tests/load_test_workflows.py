"""
Load testing script for B2B Marketing Automation Platform using Locust

Usage:
    # Run load test
    locust -f tests/load_test_workflows.py --host=http://localhost:5678

    # Run with specific user count and spawn rate
    locust -f tests/load_test_workflows.py --host=http://localhost:5678 --users 50 --spawn-rate 5

    # Run headless (no web UI)
    locust -f tests/load_test_workflows.py --host=http://localhost:5678 --users 100 --spawn-rate 10 --run-time 5m --headless
"""
import random
import time
from locust import HttpUser, task, between, tag


class ContentGenerationUser(HttpUser):
    """Simulate users generating content"""

    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks

    def on_start(self):
        """Setup test data"""
        self.campaign_id = 1  # Use existing test campaign
        self.topics = [
            "AI in Marketing",
            "Marketing Automation ROI",
            "B2B Lead Generation",
            "Content Marketing Strategies",
            "Email Marketing Best Practices"
        ]

    @tag('content', 'generation')
    @task(3)  # Weight: 3x more likely than other tasks
    def generate_content(self):
        """Test content generation workflow"""
        payload = {
            "campaign_id": self.campaign_id,
            "topic": random.choice(self.topics),
            "content_type": random.choice(["linkedin_post", "blog_post", "email_newsletter"]),
            "target_word_count": random.randint(200, 500)
        }

        with self.client.post(
            "/webhook/content-generate",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @tag('image', 'generation')
    @task(2)
    def generate_image(self):
        """Test image generation workflow"""
        payload = {
            "draft_id": random.randint(1, 100),  # Assume drafts exist
            "image_type": "social_post",
            "dimensions": random.choice(["1200x628", "1080x1080", "1920x1080"]),
            "provider": random.choice(["dalle", "midjourney"])
        }

        with self.client.post(
            "/webhook/image-generate",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @tag('review')
    @task(2)
    def submit_review(self):
        """Test review feedback workflow"""
        payload = {
            "draft_id": random.randint(1, 100),
            "action": random.choice(["approve", "revise", "reject"]),
            "feedback_text": "Test feedback from load test",
            "rating": random.randint(1, 5)
        }

        with self.client.post(
            "/webhook/review-feedback",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @tag('publish')
    @task(1)
    def publish_content(self):
        """Test publishing workflow"""
        payload = {
            "draft_id": random.randint(1, 100),
            "channels": random.sample(["linkedin", "wordpress", "email"], k=random.randint(1, 3))
        }

        with self.client.post(
            "/webhook/publish",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class ResearchUser(HttpUser):
    """Simulate users running research workflows"""

    wait_time = between(5, 10)  # Research takes longer

    @tag('research')
    @task
    def run_research(self):
        """Test research pipeline workflow"""
        payload = {
            "campaign_id": 1,
            "topics": random.sample([
                "AI marketing",
                "automation tools",
                "B2B strategies",
                "lead generation"
            ], k=2),
            "competitors": [
                "competitor1.com",
                "competitor2.com"
            ]
        }

        with self.client.post(
            "/webhook/research",
            json=payload,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Research failed: {response.status_code}")


class AnalyticsUser(HttpUser):
    """Simulate users checking analytics"""

    wait_time = between(3, 8)

    @tag('analytics')
    @task
    def track_engagement(self):
        """Test engagement tracking workflow"""
        payload = {
            "content_id": random.randint(1, 100),
            "manual_refresh": True
        }

        with self.client.post(
            "/webhook/track-engagement",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Tracking failed: {response.status_code}")


class MixedWorkloadUser(HttpUser):
    """Simulate realistic mixed workload"""

    wait_time = between(1, 5)

    tasks = {
        ContentGenerationUser: 5,  # 50% content generation
        ResearchUser: 2,            # 20% research
        AnalyticsUser: 3            # 30% analytics
    }


# Custom load shape for ramping up users
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    A step load shape that increases users in steps

    Step 1: 10 users for 60 seconds
    Step 2: 25 users for 60 seconds
    Step 3: 50 users for 60 seconds
    Step 4: 75 users for 60 seconds
    Step 5: 100 users for 120 seconds
    """

    step_time = 60
    step_load = 10
    spawn_rate = 5
    time_limit = 360  # 6 minutes total

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = (run_time // self.step_time) + 1

        if current_step <= 4:
            user_count = current_step * 25
        else:
            user_count = 100

        return (user_count, self.spawn_rate)
