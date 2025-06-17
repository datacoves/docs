import unittest
from unittest.mock import patch

from scripts.docker_images import release_images


class TestReleaseImages(unittest.TestCase):
    @patch("scripts.docker_images.load_yaml")  # Mocking the load_yaml function
    def test_release_images(self, mock_load_yaml):
        mock_load_yaml.return_value = {
            "images": {"ci-test-image": "2.0.202309271350"},
            "airbyte_images": [],
            "airflow_images": [],
            "superset_images": [],
            "observability_images": [],
            "core_images": [],
            "ci_images": {
                "ci-multiarch": "1.0.202309271350",  # Not in EXTENSIBLE_IMAGES
                "ci-basic": "1.1.202309271350",  # Is in EXTENSIBLE_IMAGES
                "datacoves/ci-airflow": "2.1.202309271350",  # Is in EXTENSIBLE_IMAGES
            },
        }

        release_name = "2.0.202309271350"
        exclude_patterns = None
        result = release_images(release_name, exclude_patterns)

        expected_result = set(
            [
                "ci-test-image:2.0.202309271350",
                "ci-multiarch:1.0.202309271350",
                "ci-basic:1.1.202309271350",
                "ci-basic:1",
                "ci-basic:1.1",
                "datacoves/ci-airflow:2.1.202309271350",
                "datacoves/ci-airflow:2.1",
                "datacoves/ci-airflow:2",
            ]
        )

        self.assertEqual(set(result), expected_result)
