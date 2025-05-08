#!/usr/bin/env python3
"""
VidID Deployment Script

This script automates the deployment of the VidID system to different cloud providers.
"""

import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vidid-deploy")

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class DeploymentManager:
    """Manager for deploying VidID to different cloud providers."""

    def __init__(self, provider, environment, config_file=None):
        """Initialize the deployment manager.
        
        Args:
            provider: Cloud provider (aws, gcp, azure)
            environment: Deployment environment (dev, staging, prod)
            config_file: Path to configuration file
        """
        self.provider = provider.lower()
        self.environment = environment.lower()
        self.config_file = config_file
        self.deployment_dir = project_root / "deployment"
        self.config = self._load_config()
        
        # Validate provider
        valid_providers = ["aws", "gcp", "azure", "local"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider: {self.provider}. Valid options: {', '.join(valid_providers)}")
        
        # Validate environment
        valid_environments = ["dev", "staging", "prod"]
        if self.environment not in valid_environments:
            raise ValueError(f"Invalid environment: {self.environment}. Valid options: {', '.join(valid_environments)}")
    
    def _load_config(self):
        """Load configuration from file.
        
        Returns:
            Dictionary with configuration values
        """
        default_config = {
            "aws": {
                "region": "us-east-1",
                "stack_name": f"vidid-{self.environment}",
                "db_username": "vidid"
            },
            "gcp": {
                "project_id": "",
                "region": "us-central1",
                "zone": "us-central1-a"
            },
            "azure": {
                "resource_group": f"vidid-{self.environment}-rg",
                "location": "eastus"
            },
            "local": {
                "docker_compose_file": "docker-compose.yml"
            }
        }
        
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                # Merge with default config
                for provider, config in user_config.items():
                    if provider in default_config:
                        default_config[provider].update(config)
        
        return default_config
    
    def deploy(self):
        """Deploy VidID to the selected provider.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deploying VidID to {self.provider} ({self.environment})")
        
        # Call provider-specific deployment method
        if self.provider == "aws":
            return self._deploy_aws()
        elif self.provider == "gcp":
            return self._deploy_gcp()
        elif self.provider == "azure":
            return self._deploy_azure()
        elif self.provider == "local":
            return self._deploy_local()
    
    def _deploy_aws(self):
        """Deploy to AWS using CloudFormation.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if AWS CLI is installed
            subprocess.run(["aws", "--version"], check=True, capture_output=True)
            
            # Get AWS CloudFormation template
            template_path = self.deployment_dir / "aws" / "cloudformation.yaml"
            if not template_path.exists():
                logger.error(f"CloudFormation template not found: {template_path}")
                return False
            
            # Prompt for DB password if not in config
            if "db_password" not in self.config["aws"]:
                import getpass
                db_password = getpass.getpass("Enter database password: ")
            else:
                db_password = self.config["aws"]["db_password"]
            
            # Deploy CloudFormation stack
            stack_name = self.config["aws"]["stack_name"]
            region = self.config["aws"]["region"]
            db_username = self.config["aws"]["db_username"]
            
            logger.info(f"Deploying CloudFormation stack: {stack_name} to {region}")
            deploy_cmd = [
                "aws", "cloudformation", "deploy",
                "--template-file", str(template_path),
                "--stack-name", stack_name,
                "--parameter-overrides",
                f"Environment={self.environment}",
                f"DBUsername={db_username}",
                f"DBPassword={db_password}",
                "--capabilities", "CAPABILITY_IAM",
                "--region", region
            ]
            
            subprocess.run(deploy_cmd, check=True)
            
            # Get stack outputs
            outputs_cmd = [
                "aws", "cloudformation", "describe-stacks",
                "--stack-name", stack_name,
                "--query", "Stacks[0].Outputs",
                "--output", "json",
                "--region", region
            ]
            
            outputs = subprocess.run(outputs_cmd, check=True, capture_output=True, text=True)
            logger.info(f"Stack outputs: {outputs.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AWS deployment failed: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
    
    def _deploy_gcp(self):
        """Deploy to GCP using Terraform.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if Terraform is installed
            subprocess.run(["terraform", "--version"], check=True, capture_output=True)
            
            # Get Terraform files
            tf_dir = self.deployment_dir / "gcp"
            if not (tf_dir / "main.tf").exists():
                logger.error(f"Terraform files not found in: {tf_dir}")
                return False
            
            # Change to Terraform directory
            os.chdir(tf_dir)
            
            # Prompt for GCP project ID if not in config
            if not self.config["gcp"]["project_id"]:
                self.config["gcp"]["project_id"] = input("Enter GCP project ID: ")
            
            # Prompt for DB password if not in config
            if "db_password" not in self.config["gcp"]:
                import getpass
                db_password = getpass.getpass("Enter database password: ")
            else:
                db_password = self.config["gcp"]["db_password"]
            
            # Initialize Terraform
            logger.info("Initializing Terraform...")
            subprocess.run(["terraform", "init"], check=True)
            
            # Create Terraform variables file
            logger.info("Creating Terraform variables...")
            with open("terraform.tfvars", "w") as f:
                f.write(f'project_id = "{self.config["gcp"]["project_id"]}"\n')
                f.write(f'region = "{self.config["gcp"]["region"]}"\n')
                f.write(f'zone = "{self.config["gcp"]["zone"]}"\n')
                f.write(f'environment = "{self.environment}"\n')
                f.write(f'db_password = "{db_password}"\n')
                
                # Replace PROJECT_ID placeholder in api_image
                api_image = self.config["gcp"].get("api_image", "gcr.io/PROJECT_ID/vidid-api:latest")
                api_image = api_image.replace("PROJECT_ID", self.config["gcp"]["project_id"])
                f.write(f'api_image = "{api_image}"\n')
            
            # Apply Terraform plan
            logger.info("Applying Terraform configuration...")
            subprocess.run(["terraform", "apply", "-auto-approve"], check=True)
            
            # Get outputs
            outputs = subprocess.run(["terraform", "output", "-json"], check=True, capture_output=True, text=True)
            logger.info(f"Terraform outputs: {outputs.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"GCP deployment failed: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
        finally:
            # Return to original directory
            os.chdir(project_root)
    
    def _deploy_azure(self):
        """Deploy to Azure (placeholder for future implementation).
        
        Returns:
            True if successful, False otherwise
        """
        logger.error("Azure deployment not implemented yet")
        return False
    
    def _deploy_local(self):
        """Deploy locally using Docker Compose.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if Docker and Docker Compose are installed
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            subprocess.run(["docker", "compose", "version"], check=True, capture_output=True)
            
            # Get Docker Compose file
            compose_file = self.config["local"]["docker_compose_file"]
            compose_path = project_root / compose_file
            if not compose_path.exists():
                logger.error(f"Docker Compose file not found: {compose_path}")
                return False
            
            # Build Docker images
            logger.info("Building Docker images...")
            build_cmd = ["docker", "compose", "-f", str(compose_path), "build"]
            subprocess.run(build_cmd, check=True)
            
            # Start containers
            logger.info("Starting containers...")
            up_cmd = ["docker", "compose", "-f", str(compose_path), "up", "-d"]
            subprocess.run(up_cmd, check=True)
            
            # Wait for containers to start
            logger.info("Waiting for containers to start...")
            time.sleep(5)
            
            # Check container status
            ps_cmd = ["docker", "compose", "-f", str(compose_path), "ps"]
            subprocess.run(ps_cmd, check=True)
            
            logger.info("Local deployment completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Local deployment failed: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
    
    def undeploy(self):
        """Remove VidID deployment from the selected provider.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Removing VidID deployment from {self.provider} ({self.environment})")
        
        # Call provider-specific undeployment method
        if self.provider == "aws":
            return self._undeploy_aws()
        elif self.provider == "gcp":
            return self._undeploy_gcp()
        elif self.provider == "azure":
            return self._undeploy_azure()
        elif self.provider == "local":
            return self._undeploy_local()
    
    def _undeploy_aws(self):
        """Remove AWS CloudFormation stack.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete CloudFormation stack
            stack_name = self.config["aws"]["stack_name"]
            region = self.config["aws"]["region"]
            
            logger.info(f"Deleting CloudFormation stack: {stack_name} from {region}")
            delete_cmd = [
                "aws", "cloudformation", "delete-stack",
                "--stack-name", stack_name,
                "--region", region
            ]
            
            subprocess.run(delete_cmd, check=True)
            
            # Wait for stack deletion
            logger.info("Waiting for stack deletion...")
            wait_cmd = [
                "aws", "cloudformation", "wait", "stack-delete-complete",
                "--stack-name", stack_name,
                "--region", region
            ]
            
            subprocess.run(wait_cmd, check=True)
            
            logger.info("Stack deleted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AWS undeployment failed: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Undeployment error: {e}")
            return False
    
    def _undeploy_gcp(self):
        """Remove GCP resources using Terraform.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get Terraform files
            tf_dir = self.deployment_dir / "gcp"
            if not (tf_dir / "main.tf").exists():
                logger.error(f"Terraform files not found in: {tf_dir}")
                return False
            
            # Change to Terraform directory
            os.chdir(tf_dir)
            
            # Destroy Terraform resources
            logger.info("Destroying Terraform resources...")
            subprocess.run(["terraform", "destroy", "-auto-approve"], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"GCP undeployment failed: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Undeployment error: {e}")
            return False
        finally:
            # Return to original directory
            os.chdir(project_root)
    
    def _undeploy_azure(self):
        """Remove Azure resources (placeholder for future implementation).
        
        Returns:
            True if successful, False otherwise
        """
        logger.error("Azure undeployment not implemented yet")
        return False
    
    def _undeploy_local(self):
        """Stop and remove local Docker containers.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get Docker Compose file
            compose_file = self.config["local"]["docker_compose_file"]
            compose_path = project_root / compose_file
            if not compose_path.exists():
                logger.error(f"Docker Compose file not found: {compose_path}")
                return False
            
            # Stop and remove containers
            logger.info("Stopping and removing containers...")
            down_cmd = ["docker", "compose", "-f", str(compose_path), "down", "--volumes", "--remove-orphans"]
            subprocess.run(down_cmd, check=True)
            
            logger.info("Local deployment removed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Local undeployment failed: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Undeployment error: {e}")
            return False


def main():
    """Main entry point for the deployment script."""
    parser = argparse.ArgumentParser(description="VidID Deployment Script")
    parser.add_argument("action", choices=["deploy", "undeploy"], help="Action to perform")
    parser.add_argument("provider", choices=["aws", "gcp", "azure", "local"], help="Cloud provider")
    parser.add_argument("--env", default="dev", choices=["dev", "staging", "prod"], help="Deployment environment")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    try:
        # Initialize deployment manager
        manager = DeploymentManager(args.provider, args.env, args.config)
        
        # Perform requested action
        if args.action == "deploy":
            success = manager.deploy()
        else:  # undeploy
            success = manager.undeploy()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
