Running two Redis instances on a single Linux server involves the following steps:

1. **Install Redis**:
   If you haven’t installed Redis, you can do so using the package manager of your Linux distribution. Here's how to do it on Ubuntu:

   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

2. **Configure the First Instance**:
   The default configuration file for Redis is usually located at `/etc/redis/redis.conf`. You can make sure the configuration suits your needs, especially noting the `port` directive which defaults to `6379`.

3. **Configure the Second Instance**:
   - **Create a new configuration file**:

     Copy the original configuration file to create a new one for the second instance:

     ```bash
     sudo cp /etc/redis/redis.conf /etc/redis/redis2.conf
     ```

   - **Modify the new configuration file**:

     Open the new configuration file in an editor:

     ```bash
     sudo nano /etc/redis/redis2.conf
     ```

     Change the following settings:

     - `port`: Set it to a different value, say `6380` (or any other available port).
     - `pidfile`: Change it to `/var/run/redis/redis2.pid`.
     - `logfile`: Change it to `/var/log/redis/redis2.log`.
     - `dir`: This is where Redis saves dump files, set it to a different directory or make sure the filenames inside are unique for each instance.

4. **Configure Systemd to Manage Both Instances**:
   If you're using `systemd` to manage services, you might want to create separate service units for each Redis instance:

   - **Create a new service file for the second instance**:

     ```bash
     sudo cp /lib/systemd/system/redis-server.service /etc/systemd/system/redis2-server.service
     ```

   - **Edit the new service file**:

     ```bash
     sudo nano /etc/systemd/system/redis2-server.service
     ```

     Change the following:

     ```ini
     [Service]
     ExecStart=/usr/bin/redis-server /etc/redis/redis2.conf
     ```

     Save and close the editor.

   - **Reload systemd** to recognize the new service:

     ```bash
     sudo systemctl daemon-reload
     ```

   - **Start and enable the second Redis instance**:

     ```bash
     sudo systemctl start redis2-server
     sudo systemctl enable redis2-server
     ```

Now you have two Redis instances running on your server, one on port `6379` and another on port `6380` (or whichever ports you've chosen).

Remember, running multiple Redis instances on a single server will consume more memory and resources, so ensure your server is properly sized to handle the load.