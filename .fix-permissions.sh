#!/bin/bash
# Script to fix permissions in exceptions directory
# Run this if you encounter permission issues

echo "Fixing ownership of all files in /home/pw/repos/exceptions/ ..."
sudo chown -R pw:pw /home/pw/repos/exceptions/

echo "Setting proper directory permissions..."
sudo chmod -R u+rwX,g+rX,o+rX /home/pw/repos/exceptions/

echo "✅ Permission fix complete!"
echo "All files in /home/pw/repos/exceptions/ now owned by user 'pw'"