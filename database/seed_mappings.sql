-- Seed mappings for TEAM_TO_RESOURCE_TYPES
-- This maps incident teams to Scaleway resource types

-- Insert team to resource type mappings
-- These are used to match incidents to resources via GetFilteredCounters API

INSERT INTO team_resource_mappings (team, resource_type, product_type)
VALUES
    -- Compute / Instance team
    ('compute', 'instance', 1),
    ('compute', 'instance_gpu', 2),
    ('compute', 'instance_volume_l_ssd', 84),
    ('compute', 'instance_volume_scratch', 85),
    ('compute', 'instance_template', 91),
    ('compute', 'autoscaling_group', 87),
    
    -- Network team
    ('network', 'public_gateway', 14),
    ('network', 'ip', 48),
    ('network', 'private_networks', 49),
    ('network', 'vpc', 50),
    ('network', 'ipam', 61),
    ('network', 'vpc_peering_connector', 88),
    ('network', 'ili_port', 77),
    ('network', 'ili_link', 75),
    ('network', 'ili_routing_policy', 74),
    ('network', 'ili_loa', 78),
    ('network', 'ili_connection', 79),
    ('network', 'svpn_vpn_gateways', 80),
    ('network', 'svpn_customer_gateways', 81),
    ('network', 'svpn_connections', 82),
    ('network', 'svpn_routing_policies', 83),
    ('network', 'flexible_ip', 13),
    ('network', 'dedibox', 16),
    
    -- Storage team
    ('storage', 'sbs_volume', 58),
    ('storage', 'sbs_volume_storage', 62),
    ('storage', 'sbs_snapshot', 59),
    ('storage', 'sbs_snapshot_storage', 64),
    ('storage', 'sfs_file_system', 66),
    ('storage', 'sfs_file_system_storage', 67),
    ('storage', 'object_storage', 3),
    ('storage', 'object_storage_bucket', 55),
    ('storage', 'snapshots', 43),
    ('storage', 'images', 44),
    ('storage', 'volumes', 45),
    
    -- Database team
    ('database', 'relational_database', 5),
    ('database', 'rdb_snapshots', 52),
    ('database', 'rdb_backups', 53),
    ('database', 'redis', 19),
    ('database', 'serverless_db', 57),
    ('database', 'mongodb', 70),
    ('database', 'mongodb_snapshots', 71),
    ('database', 'dtwh_clickhouse', 72),
    ('database', 'searchdb', 92),
    
    -- Container / Kapsule team
    ('container', 'kubernetes', 7),
    ('container', 'containers', 17),
    ('container', 'containers_ns', 32),
    ('container', 'registry', 6),
    ('container', 'registry_ns', 31),
    
    -- Load Balancer team
    ('load_balancer', 'load_balancer', 4),
    ('load_balancer', 'load_balancer_ip', 51),
    
    -- Serverless team
    ('serverless', 'serverless', 10),
    ('serverless', 'functions', 18),
    ('serverless', 'functions_ns', 33),
    ('serverless', 'serverless_jobs', 60),
    ('serverless', 'edge_services_pipeline', 63),
    
    -- Observability / Monitoring team
    ('monitoring', 'observability_data_source', 68),
    ('monitoring', 'observability_exporter', 89),
    ('monitoring', 'observability_token', 24),
    ('monitoring', 'observability_alert_contact_point', 25),
    ('monitoring', 'observability_grafana_user', 26),
    
    -- Security / IAM team
    ('iam', 'iam_api_keys', 36),
    ('iam', 'iam_ssh_keys', 37),
    ('iam', 'iam_users', 38),
    ('iam', 'iam_applications', 39),
    ('iam', 'iam_groups', 40),
    ('iam', 'iam_policies', 41),
    ('iam', 'iam_permission_sets', 42),
    ('iam', 'secret', 27),
    ('iam', 'secret_version', 28),
    ('iam', 'key', 29),
    ('iam', 'key_version', 30),
    ('iam', 'key_rotation', 76),
    ('iam', 'managed_key', 34),
    ('iam', 'managed_key_version', 35),
    
    -- Messaging team
    ('messaging', 'messaging', 21),
    ('messaging', 'kafka', 73),
    ('messaging', 'transactional_email', 20),
    
    -- Webhosting team
    ('webhosting', 'webhosting', 22),
    
    -- Internal services team
    ('internal-services', 'domain', 11),
    ('internal-services', 'smart_labeling', 15),
    ('internal-services', 'datalab', 90),
    ('internal-services', 'managed_inference', 65),
    ('internal-services', 'ifr_custom_model', 86),
    
    -- SRE team (covers all types)
    ('sre', 'instance', 1),
    ('sre', 'kubernetes', 7),
    ('sre', 'load_balancer', 4),
    ('sre', 'object_storage', 3),
    
    -- Platform team
    ('platform', 'instance', 1),
    ('platform', 'security_groups', 46),
    ('platform', 'placement_groups', 47),
    ('platform', 'instance_ip', 54),
    
    -- Dedibox team
    ('dedibox', 'dedibox', 16),
    ('dedibox', 'webhosting', 22),
    
    -- Shared hosting / PaaS team
    ('shared-hosting-paas', 'webhosting', 22),
    ('shared-hosting-paas', 'containers', 17),
    
    -- Object Storage team
    ('object-storage', 'object_storage', 3),
    ('object-storage', 'object_storage_bucket', 55),
    
    -- Cloud Compute team
    ('cloud-compute', 'instance', 1),
    ('cloud-compute', 'baremetal', 8),
    ('cloud-compute', 'apple_silicon', 12),
    
    -- Hardware team
    ('hardware', 'baremetal', 8),
    ('hardware', 'dedibox', 16),
    
    -- Billing team
    ('billing', 'instance', 1),
    ('billing', 'object_storage', 3),
    
    -- User Accounts team
    ('user-accounts', 'iam_users', 38),
    ('user-accounts', 'iam_api_keys', 36)
ON CONFLICT (team, resource_type) DO NOTHING;

-- Note: You'll need to create the team_resource_mappings table first if it doesn't exist
-- Uncomment the following if you want to store mappings in DB:
/*
CREATE TABLE IF NOT EXISTS team_resource_mappings (
    id SERIAL PRIMARY KEY,
    team VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    product_type INTEGER NOT NULL,
    UNIQUE(team, resource_type)
);
*/