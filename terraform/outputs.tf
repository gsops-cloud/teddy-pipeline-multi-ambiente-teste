output "ecs_cluster_name" {
  description = "Nome do cluster ECS"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Nome do serviço ECS"
  value       = aws_ecs_service.main.name
}

output "ecs_cluster_arn" {
  description = "ARN do cluster ECS"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_arn" {
  description = "ARN do serviço ECS"
  value       = aws_ecs_service.main.id
}

output "task_definition_arn" {
  description = "ARN da task definition"
  value       = aws_ecs_task_definition.main.arn
}

output "cloudwatch_log_group" {
  description = "Nome do grupo de logs CloudWatch"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "alb_dns_name" {
  description = "DNS name do Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "URL do Application Load Balancer"
  value       = "http://${aws_lb.main.dns_name}"
}