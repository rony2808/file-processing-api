output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.app.public_ip
}

output "api_url" {
  description = "URL of the API health endpoint"
  value       = "http://${aws_instance.app.public_ip}:8000/health"
}
