# Encrypted config files
In your code, please use the `project.txt` files directly, but on changes/commits
use the commands below to encrypt the file and only commit the `project_encrypted.txt` file.

Password to decrypt existing files can be requested at Maarten Pronk or Gerrit Hendriksen and should be stored in KeePass.

```bash
### encrypt
ansible-vault encrypt project.txt --output project_encrypted.txt

### decrypt
ansible-vault decrypt project_encrypted.txt --output project.txt
```
