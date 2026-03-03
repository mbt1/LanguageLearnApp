output "instance_public_ip" {
  description = "Public IP address of the test instance. Use as the Playwright base URL."
  value       = aws_instance.test.public_ip
}

output "health_url" {
  description = "Health check URL to poll until the instance is ready."
  value       = "http://${aws_instance.test.public_ip}/v1/health"
}
