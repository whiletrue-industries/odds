resource "contabo_secret" "server_password" {
  name = "ckangpt_server_password"
  type = "password"
  value = var.server_password
  lifecycle {
    ignore_changes = [value]
  }
}

resource "contabo_instance" "server" {
  display_name  = "ckangpt"
  product_id    = "V2"  # VPS M SSD: 6 vCPU, 16 GB RAM, 400 GB SSD ~14$ per month
  region        = "EU"
  period        = 1  # 8.49$ one time setup fee

  # export CNTB_ACCESS_TOKEN="$(curl -d "client_id=$CNTB_OAUTH2_CLIENT_ID" -d "client_secret=$CNTB_OAUTH2_CLIENT_SECRET" \
  #   --data-urlencode "username=$CNTB_OAUTH2_USER" \
  #   --data-urlencode "password=$CNTB_OAUTH2_PASS" \
  #   -d 'grant_type=password' \
  #   'https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token' | jq -r .access_token)"
  # curl -X GET 'https://api.contabo.com/v1/compute/images?size=9999' \
  #   -H 'Content-Type: application/json' \
  #   -H "Authorization: Bearer ${CNTB_ACCESS_TOKEN}" \
  #   -H 'x-request-id: 04e0f898-37b4-48bc-a794-1a57abe6aa31' -H 'x-trace-id: 123213' | jq -r '.data[] | "\(.description) \(.imageId)"' \
  #       | grep "Ubuntu 22.04 (LTS)"
  image_id = "afecbb85-e2fc-46f0-9684-b46b1faf00bb"
  root_password = contabo_secret.server_password.id
}

output "server_ip" {
  value = contabo_instance.server.ip_config[0].v4[0].ip
}

output "server_root_user" {
  value = "admin"
}

locals {
  ssh_keys = [
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDAU8I7VawhtQ4suRZGbMLTNkwqHWQe5xASYlyBje1UX1yUv88dbHnIh736O4DlbNODhPdaDkYxofwbpai5o4CTTbuWiqjc5duKG+tb1dSu89+2HYbufVIkdIiZCNZN3A2fDNPkXzX8tjVsXC7RRjgZMYZDpAgytQPuP8HC9HK/rcfhaYIZYYveEydXZj+P/XpKGGmIpaDCzjG0s3vZFw4p2tAOnmuzhbp1+Zl4wgWi83Z7CT5bsMQKATxT6WdkByTE9cHaCfaxWhF9EsoQl3f1itoGpW6EYAD7rHnY8YtDTNeLUAGj513mqa2UkjsXlOdX8aCDtOIuQUgHkAnwpXO+Cu6kxrFf8yi6R+W5uHjN2aEMhPBiM9Iz42Os7WQrMybsqzxvBHtkqpCbi4Y81Rcbs8LJrAy6AZ7D2YhPbycJXJZu+DQ1dy6OtE2NIAWzofD6aVYxzK8VzSA2tw0dCbhdOUOEjIhguFA4Z4IQennVkAHBNF/SHmjsBxPOPcHNz+geaCz4Q1otgb9ZRf8HuPkf/jHuG3h+5M0Gn7TUdDmWIDoOqN+CslJAkhffzwl/MtT8yXg6etl+9l+2ngVtfSYkxPOON0XpgZxdAWZwhJFKEzZlPc5M0+lA9Wy63/YMU4h1EA0QxE3fIa2Ojtj1Pmshlp0BTJx09sdOiv9oNogfRw== ori@uumpa.com",
  ]
  ssh_connection = {
    user = "admin"
    host = contabo_instance.server.ip_config[0].v4[0].ip
    password = contabo_secret.server_password.value
  }
}

resource "null_resource" "set_authorised_keys" {
  depends_on = [contabo_instance.server]
  connection {
    user = local.ssh_connection.user
    host = local.ssh_connection.host
    password = local.ssh_connection.password
  }
  provisioner "remote-exec" {
    inline = [
      "echo '${join("\n", local.ssh_keys)}' > ~/.ssh/authorized_keys"
    ]
  }
}

resource "null_resource" "install_k0s" {
  depends_on = [contabo_instance.server]
  connection {
    user = local.ssh_connection.user
    host = local.ssh_connection.host
    password = local.ssh_connection.password
  }
  provisioner "remote-exec" {
    inline = [
      "#!/bin/bash",
#      "curl -sSLf https://get.k0s.sh | sudo sh",
#      "sudo k0s install controller --single",
#      "sudo k0s start",
#      "sudo apt install -y jq",
#      "sudo shutdown -r now",
      "sudo k0s status",
      "[ \"$(sudo k0s status -o json | jq -r .WorkerToAPIConnectionStatus.Success)\" == \"true\" ]",
      "sudo k0s kubectl get nodes",
    ]
  }
}

