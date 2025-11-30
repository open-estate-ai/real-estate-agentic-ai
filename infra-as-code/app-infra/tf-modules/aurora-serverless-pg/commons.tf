## Local variables
locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.project_name))
}
