while true; do
    # Run the updater.py script
    python updater.py

    # Check if there are any changes
    if [[ $(git status --porcelain) ]]; then
        # Add the changes
        git add README.md

        # Commit the changes
        git commit -m "Auto-update README.md"

        # Push the changes
        git push origin main  # Change 'main' to your branch name if different

        echo "Changes pushed successfully."
    else
        echo "No changes to push."
    fi

    # Wait for 1 hour (3600 seconds)
    sleep 3600
done