terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>4.65.0"
    }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.AWS_REGION
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket                   = var.S3_BUCKET_NAME
  acl                      = "private"
  force_destroy            = true
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
    "MARKET_WEBHOOK_URL" = var.MARKET_WEBHOOK_URL
    "CLUB_WEBHOOK_URL"   = var.CLUB_WEBHOOK_URL
    "S3_BUCKET_ARN"      = module.s3_bucket.s3_bucket_id
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
      source_arn = module.eventbridge.eventbridge_schedule_arns["inventory-checker-cron"]
    }
  }

  tags = {
    Name = "inventory-checker"
  }
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  bus_name = "inventory-checker"

  attach_lambda_policy = true
  lambda_target_arns   = [module.lambda_function.lambda_function_arn]

  schedules = {
    inventory-checker-cron = {
      description         = "Trigger for inventory checker lambda function"
      schedule_expression = "cron(0 9,21 * * ? *)"
      timezone            = "America/El_Salvador"
      arn                 = module.lambda_function.lambda_function_arn
      input               = jsonencode({ "job" : "cron-by-schedule" })
    }
  }

  create_bus = true

  tags = {
    Name = "inventory-checker"
  }
}
