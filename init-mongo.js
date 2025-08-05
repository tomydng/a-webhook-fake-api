// MongoDB initialization script
db = db.getSiblingDB("webhook_db");

// Create collection if it doesn't exist
db.createCollection("webhook_requests");

// Create indexes for better performance
db.webhook_requests.createIndex({ timestamp: -1 });
db.webhook_requests.createIndex({ method: 1 });
db.webhook_requests.createIndex({ path: 1 });
db.webhook_requests.createIndex({ "headers.x-signature": 1 });

print("Database initialized successfully");
