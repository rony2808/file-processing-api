terraform {
  backend "s3" {
    bucket       = "rony2808-terraform-state-file-processing"
    key          = "infra/terraform.tfstate"
    region       = "eu-central-1"
    use_lockfile = true
  }
}
