How to update bballwill.com

1. Edit on GitHub — push your changes to the repo.

2. Open Cloud Shell (server is under will.luttrell@gmail.com):
   https://console.cloud.google.com/compute/instances?cloudshell=true&chat=true&project=basketball-website
   Confirm the project at the top is basketball-website.

3. (Optional) List VMs to get the instance name and zone:
   ```bash
   gcloud compute instances list
   ```

4. SSH into the VM (use NAME and ZONE from step 3; current values below):
   ```bash
   gcloud compute ssh instance-20250213-231711 --zone=us-central1-c
   ```
   First time only: answer Y to create SSH keys; passphrase can be empty.

5. On the VM, go to the app directory and pull as the service user:
   ```bash
   cd /home/liem/bballwill
   sudo -u liem git pull
   ```
   Use `sudo -u liem git pull` (not plain `git pull`) so the repo stays owned by liem.

6. Restart the app:
   ```bash
   sudo systemctl restart bballwill.service
   ```

7. Exit the VM when done:
   ```bash
   exit
   ```
