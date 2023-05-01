terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>4.65.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = var.s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
  tags = {
    Name = "inventory-checker"
  }
}

module "lambda_function" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~>4.16.0"

  function_name = "inventory-checker1"
  description   = "Inventory checker lambda function"
  handler       = "app.lambda_handler"
  runtime       = "python3.10"
  timeout       = 300
  publish       = true

  source_path = [
    "./app/app.py",
    {
      path             = "./app",
      pip_requirements = true,
    }
  ]

  environment_variables = {
    "WEBHOOK_URL"   = var.webhook_url
    "S3_BUCKET_ARN" = module.s3_bucket.s3_bucket_id
  }
  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect = "Allow",
      actions = [
        "s3:GetObject"
      ],
      resources = ["${module.s3_bucket.s3_bucket_arn}/*"]
    }
  }

  allowed_triggers = {
    EventBridge = {
      principal  = "events.amazonaws.com"
      source_arn = module.eventbridge.eventbridge_rule_arns["crons"]
    }
  }

  tags = {
    Name = "inventory-checker"
  }
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  create_bus = false

  rules = {
    crons = {
      description         = "Trigger for Inventory checker lambda"
      schedule_expression = "cron(0 9,21 * * ? *)"
    }
  }

  targets = {
    crons = [
      {
        name  = "inventory-checker-cron"
        arn   = module.lambda_function.lambda_function_arn
        input = jsonencode({ "job" : "cron-by-schedule" })
      }
    ]
  }

  tags = {
    Name = "inventory-checker"
  }
}
