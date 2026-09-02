variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Project name used to prefix resources"
  type        = string
  default     = "file-processing"
}

variable "my_ip" {
  description = "Your public IP for SSH access (CIDR format)"
  type        = string

}

variable "docker_username" {
  description = "Docker Hub username for pulling images"
  type        = string
  default     = "ronk1234"
}

variable "alert_email" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
}
