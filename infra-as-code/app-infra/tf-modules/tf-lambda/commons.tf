## Local variables
locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.lambda_name))
  lambda_backend_abs_dir          = "${path.module}/${var.backend_directory}"
  lambda_src_abs_dir              = "${local.lambda_backend_abs_dir}/${var.lambda_src_dir}"
  lambda_src_files                = fileset(local.lambda_src_abs_dir, "**")
  # Combined content hash over all files
  lambda_src_hash = sha1(
    join(
      "",
      [
        for f in local.lambda_src_files :
        filesha1("${local.lambda_src_abs_dir}/${f}")
      ]
    )
  )

  image_tag = local.lambda_src_hash
}


