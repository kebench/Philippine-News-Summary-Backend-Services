output "schedule_arn" {
  description = "ARN of the EventBridge schedule."
  value       = aws_scheduler_schedule.schedule.arn
}

output "schedule_name" {
  description = "Name of the EventBridge schedule."
  value       = aws_scheduler_schedule.schedule.name
}