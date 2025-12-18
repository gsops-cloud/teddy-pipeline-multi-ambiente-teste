variable "environment" {
  description = "Ambiente de deploy (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment deve ser dev, staging ou prod."
  }
}

variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "docker_image" {
  description = "Nome da imagem Docker (sem tag)"
  type        = string
  default     = ""
}

variable "docker_image_tag" {
  description = "Tag da imagem Docker"
  type        = string
  default     = "latest"
}

variable "container_port" {
  description = "Porta do container"
  type        = number
  default     = 8080
}

variable "task_cpu" {
  description = "CPU para a task ECS (em unidades de 256, ex: 256, 512, 1024)"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memória para a task ECS (em MB)"
  type        = number
  default     = 512
}

variable "service_desired_count" {
  description = "Número desejado de instâncias do serviço"
  type        = number
  default     = 1
}

variable "log_retention_days" {
  description = "Dias de retenção dos logs no CloudWatch"
  type        = number
  default     = 7
}

variable "ssm_parameters" {
  description = "Mapeamento de variáveis de ambiente para parâmetros SSM"
  type        = map(string)
  default     = {}
}