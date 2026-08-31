terraform {
  backend "s3" {
    bucket       = "rony2808-terraform-state-file-processing"
    key          = "infra/terraform.tfstate"
    region       = var.aws_region
    use_lockfile = true
  }
}
