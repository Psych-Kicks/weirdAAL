import boto3
import botocore
import pprint
import sys

pp = pprint.PrettyPrinter(indent=5, width=80)

#from http://docs.aws.amazon.com/general/latest/gr/rande.html
regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',  ]

region = 'us-east-1'
def get_accountid(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    client = boto3.client("sts", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    account_id = client.get_caller_identity()["Account"]
    return account_id

#NOT QUITE WORKING YET
#def get_username(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY):
#    client = boto3.client("sts", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#    username = client.get_caller_identity()["Arn"].split(':')[5]
#    print username
#    return username

def check_root_account(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    client = boto3.client('iam', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
    try:
        acct_summary = client.get_account_summary()
        if acct_summary:
            print("Root Key!!! [or IAM access]")
            print("Printing Account Summary")
            pp.pprint(acct_summary['SummaryMap'])

        client_list = client.list_users()
        if client_list:
            print("Printing Users")
            pp.pprint(client_list['Users'])
        
        print("Checking for console access")
        for user in client_list['Users']:
            
            try:
                profile = client.get_login_profile(UserName=user['UserName'])
                if profile:
                    print('User %s likely has console access and the password can be reset :-)' % user['UserName'])
                    print("Checking for MFA on account")
                    mfa = client.list_mfa_devices(UserName=user['UserName'])
                    print mfa['MFADevices']
            
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    print("[-]: user '%s' likely doesnt have console access" % user['UserName'])
                else:
                    print "Unexpected error: %s" % e
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            sys.exit("The AWS KEY IS INVALID. Exiting")
        elif e.response['Error']['Code'] == 'AccessDenied':
            print('%s : Is NOT a root key' % AWS_ACCESS_KEY_ID)
        else:
            print "Unexpected error: %s" % e

def generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, service, tests):
    actions = []
    try:
        client = boto3.client(service, aws_access_key_id = AWS_ACCESS_KEY_ID, aws_secret_access_key = AWS_SECRET_ACCESS_KEY, region_name=region)
    except Exception as e:
        #print('Failed to connect: "{}"' .format(e.error_message))
        print('Failed to connect: "{}"' .format(e))
        return actions
    
    actions = generic_method_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, service, tests)
    if actions:
        print ("\n[+] {} Actions allowed are [+]" .format(service))
        print (actions)
        print ("\n")
    else:
        print ("\n[-] No {} actions allowed [-]" .format(service))
        print ("\n")
    return actions

def generic_method_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, service, tests):
    actions = []
    client = boto3.client(service, aws_access_key_id = AWS_ACCESS_KEY_ID, aws_secret_access_key = AWS_SECRET_ACCESS_KEY, region_name=region)
    for api_action, method_name, args, kwargs in tests:
        try:
            method = getattr(client, method_name)
            method(*args, **kwargs)
            #print method --wont return anything on dryrun
        except botocore.exceptions.EndpointConnectionError as e:
            print e
            continue
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'DryRunOperation':
                print('{} IS allowed' .format(api_action))
                actions.append(api_action)
            if e.response['Error']['Code'] == 'ClusterNotFoundException':
                print('{} IS allowed but you need to specify a cluster name' .format(api_action))
                actions.append(api_action)
            else:
                print e
                continue 
        else:
            print('{} IS allowed' .format(api_action))
            actions.append(api_action)
    return actions

#http://boto3.readthedocs.io/en/latest/reference/services/acm.html
def brute_acm_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ACM Permissions ###")
    tests = [('ListCertificates', 'list_certificates', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'acm', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/apigateway.html
def brute_apigateway_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating APIGateway Permissions ###")
    tests = [('GetAccount', 'get_account', (), {}, ), 
             ('GetApiKeys', 'get_api_keys', (), {}, ), 
             ('GetClientCertificates', 'get_client_certificates', (), {}, ),
             ('GetDomainNames', 'get_domain_names', (), {}, ),
             ('GetRestApis', 'get_rest_apis', (), {}, ), 
             ('GetSdkTypes', 'get_sdk_types', (), {}, ), 
             ('GetUsagePlans', 'get_usage_plans', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'apigateway', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/appstream.html
def brute_appstream_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating APPStream Permissions ###")
    tests = [('DescribeFleets', 'describe_fleets', (), {}, ),
             ('DescribeImages', 'describe_images', (), {}, ), 
             ('DescribeStacks', 'describe_stacks', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'appstream', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/athena.html
def brute_athena_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Athena Permissions ###")
    tests = [('ListNamedQueries', 'list_named_queries', (), {}, ),
             ('ListQueryExecutions', 'list_query_executions', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'athena', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/autoscaling.html
def brute_autoscaling_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Autoscaling Permissions ###")
    tests = [('DescribeAccountLimits', 'describe_account_limits', (), {}, ),
             ('DescribeAdjustmentTypes', 'describe_adjustment_types', (), {}, ),
             ('DescribeAutoScalingInstances', 'describe_auto_scaling_instances', (), {}, ),
             ('DescribeAutoScalingGroups', 'describe_auto_scaling_groups', (), {}),
             ('DescribeLaunchConfigurations', 'describe_launch_configurations', (), {}),
             ('DescribeScheduledActions', 'describe_scheduled_actions', (), {}),
             ('DescribeTags', 'describe_tags', (), {}, ),
             ('DescribeTerminationPolicyTypes', 'describe_termination_policy_types', (), {}, ),
             ('DescribePolicies', 'describe_policies', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'autoscaling', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/batch.html
def brute_batch_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Batch Permissions ###")
    tests = [('DescribeComputeEnvironments', 'describe_compute_environments', (), {}, ),
             ('DescribeJobDefinitions', 'describe_job_definitions', (), {}, ),  
             ('DescribeJobQueues', 'describe_job_queues', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'batch', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/budgets.html
def brute_budgets_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Budgets Permissions ###")
    account_id = get_accountid(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    tests = [('DescribeBudgets', 'describe_budgets', (), {'AccountId':account_id}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'budgets', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cloudformation.html
def brute_cloudformation_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CLoudFormation Permissions ###")
    tests = [('ListStacks', 'list_stacks', (), {} ),
             ('DescribeStacks', 'describe_stacks', (), {} ), 
             ('DescribeStackEvents', 'describe_stack_events', (), {} ), 
             ('DescribeStackResources', 'describe_stack_resources', (), {} ),
             ('ListExports', 'list_exports', (), {} ),
             ('DescribeAccountLimits', 'describe_account_limits', (), {} ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cloudformation', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cloudfront.html
def brute_cloudfront_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CLoudFront Permissions ###")
    tests = [('ListDistributions', 'list_distributions', (), {}), 
             ('ListCloudFrontOriginAcessIdentities', 'list_cloud_front_origin_access_identities', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cloudfront', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cloudhsm.html
def brute_cloudhsm_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CloudHSM Permissions ###")
    tests = [('DescribeHsm', 'describe_hsm', (), {}),
             ('ListHsms', 'list_hsms', (), {}),
             ('ListHapgs', 'list_hapgs', (), {}),
             ('DescribeLunaClient', 'describe_luna_client', (), {}),
             ('ListLunaClients', 'list_luna_clients', (), {}),
             ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cloudhsm', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cloudsearch.html
def brute_cloudsearch_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CloudSearch Permissions ###")
    tests = [('DescribeDomains', 'describe_domains', (), {}, ), 
             ('ListDomainNames', 'list_domain_names', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cloudsearch', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cloudtrail.html
def brute_cloudtrail_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CloudTrail Permissions ###")
    tests = [('DescribeTrails', 'describe_trails', (), {}, ), 
             ('ListPublicKeys', 'list_public_keys', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cloudtrail', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cloudwatch.html
def brute_cloudwatch_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CloudWatch Permissions ###")
    tests = [('ListMetrics', 'list_metrics', (), {}, ), 
             ('DescribeAlarmHistory', 'describe_alarm_history', (), {}, ),
             ('DescribeAlarms', 'describe_alarms', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cloudwatch', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html
def brute_codebuild_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CodeBuild Permissions ###")
    tests = [('ListBuilds', 'list_builds', (), {}, ), 
             ('ListCuratedEnvironmentImages', 'list_curated_environment_images', (), {}, ),  
             ('ListProjects', 'list_projects', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'codebuild', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/codecommit.html
def brute_codecommit_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CodeCommit Permissions ###")
    tests = [('ListRepositories', 'list_repositories', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'codecommit', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/codedeploy.html
def brute_codedeploy_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CodeDeploy Permissions ###")
    tests = [('ListApplications', 'list_applications', (), {}, ), 
             ('ListDeployments', 'list_deployments', (), {}, ), 
             ('ListDeploymentsConfigs', 'list_deployment_configs', (), {}, ), 
             #('ListGitHubAccountTokenNames', 'list_git_hub_account_token_names', (), {}, ), #returning an error no function of that name
             ('ListOnPremisesInstances', 'list_on_premises_instances', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'codedeploy', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/codepipeline.html
def brute_codepipeline_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CodePipeline Permissions ###")
    tests = [('ListPipelines', 'list_pipelines', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'codepipeline', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/codestar.html
def brute_codestar_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CodeStar Permissions ###")
    tests = [('ListProjects', 'list_projects', (), {}, ),  
             ('ListUerProfiles', 'list_user_profiles', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'codestar', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cognito-identity.html
def brute_cognitoidentity_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Cognito-Identity Permissions ###")
    tests = [('ListIdentityPools', 'list_identity_pools', (), {'MaxResults':1}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cognito-identity', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cognito-idp.html
def brute_cognitoidp_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CognitoIdentityProvider Permissions ###")
    tests = [('ListUserPools', 'list_user_pools', (), {'MaxResults':1}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cognito-idp', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/cognito-sync.html
def brute_cognitosync_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CognitoSync Permissions ###")
    tests = [('ListIdentityPoolUsage', 'list_identity_pool_usage', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cognito-sync', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/config.html
def brute_configservice_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ConfigService Permissions ###")
    tests = [('DescribeComplianceByConfigRule', 'describe_compliance_by_config_rule', (), {}, ),
             ('DescribeComplianceByResource', 'describe_compliance_by_resource', (), {}, ), 
             ('DescribeConfigRuleEvaluationStatus', 'describe_config_rule_evaluation_status', (), {}, ),
             ('DescribeConfigurationRecorders', 'describe_configuration_recorders', (), {}, ),  
             ('DescribeConfigRules', 'describe_config_rules', (), {}, ), 
             ('DescribeConfigurationRecorderStatus', 'describe_configuration_recorder_status', (), {}, ), 
             ('DescribeDeliveryChannelStatus', 'describe_delivery_channel_status', (), {}, ),
             ('DescribeDeliveryChannels', 'describe_delivery_channels', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'config', tests)

#Doesnt seem to be working
#http://boto3.readthedocs.io/en/latest/reference/services/cur.html
def brute_costandusagereportservice_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CostandUsageReportService Permissions ###")
    tests = [('DescribeReportDefinitions', 'describe_report_definitions', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'cur', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/datapipeline.html
def brute_datapipeline_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DataPipeline Permissions ###")
    tests = [('ListPipelines', 'list_pipelines', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'datapipeline', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/devicefarm.html
#http://docs.aws.amazon.com/general/latest/gr/rande.html#devicefarm_region
def brute_devicefarm_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DeviceFarm Permissions ###")
    tests = [('ListProjects', 'list_projects', (), {}, ), 
             ('ListDevices', 'list_devices', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'devicefarm', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/directconnect.html
def brute_directconnect_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DirectConnect Permissions ###")
    tests = [('DescribeConnections', 'describe_connections', (), {}, ), 
             ('DescribeLags', 'describe_lags', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'directconnect', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/discovery.html
def brute_applicationdiscoveryservice_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ApplicationDiscoveryService Permissions ###")
    tests = [('DescribeAgents', 'describe_agents', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'discovery', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/dms.html
def brute_dms_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DatabaseMigrationService Permissions ###")
    tests = [('DescribeAccountAttributes', 'describe_account_attributes', (), {}, ), 
             ('DescribeEvents', 'describe_events', (), {}, ), 
             ('DescribeConnections', 'describe_connections', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'dms', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/ds.html
def brute_directoryservice_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DirectoryService Permissions ###")
    tests = [('DescribeDirectories', 'describe_directories', (), {}, ), 
             ('DescribeSnapshots', 'describe_snapshots', (), {}, ), 
             ('DescribeTrusts', 'describe_trusts', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'ds', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html
def brute_dynamodb_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DynamoDB Permissions ###")
    tests = [('ListTables', 'list_tables', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'dynamodb', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/dynamodbstreams.html
def brute_dynamodbstreams_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating DynamoDBStreamsPermissions ###")
    tests = [('ListStreams', 'list_streams', (), {}, ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'dynamodbstreams', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#client
def brute_ec2_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating EC2 Permissions ###")
    tests = [('DescribeInstances', 'describe_instances', (), {'DryRun':True}, ),
             ('DescribeInstanceStatus', 'describe_instance_status', (), {'DryRun':True}, ),
             ('DescribeImages', 'describe_images', (), {'DryRun':True, 'Owners': ['self',]} ),
             ('CreateImage', 'create_image', (), {'InstanceId':'i-0ffffeeeeaa11e111','Name':'testimage','DryRun':True}, ),
             ('DescribeVolumes', 'describe_volumes', (), {'DryRun':True}, ),
             ('CreateVolume', 'create_volume', (), {'AvailabilityZone':'us-east1','Size':8,'DryRun':True}, ),
             ('DescribeSnapshots', 'describe_snapshots', (), {'DryRun':True, 'OwnerIds': ['self',]} ),
             ('CreateSnapshot', 'create_snapshot', (), {'VolumeId':'vol-05777eab71bc97dcb', 'DryRun':True}, ),
             ('DescribeAccountAttributes', 'describe_account_attributes', (), {'DryRun':True}, ),
             ('DescribeAccounts', 'describe_addresses', (), {'DryRun':True}, ),
             ('DescribeAddresses','describe_addresses', (), {'DryRun':True}, ),
             ('DescribeAvailabilityZones', 'describe_availability_zones', (), {'DryRun':True}, ),
             ('DescribeBundleTasks', 'describe_bundle_tasks', (), {'DryRun':True}, ),
             ('DescribeClassicLinkInstances','describe_classic_link_instances', (), {'DryRun':True}, ),
             ('DescribeConversionTasks', 'describe_conversion_tasks', (), {'DryRun':True}, ),
             ('DescribeCustomerGateways', 'describe_customer_gateways', (), {'DryRun':True}, ),
             ('DescribeDhcpOptions', 'describe_dhcp_options', (), {'DryRun':True}, ),
             ('DescribeEgressOnlyInternetGateways','describe_egress_only_internet_gateways', (), {'DryRun':True}, ),

             #The above is more than enough to decide that all/almost all EC2 permissions are there but
             #I'm putting all of them so they can be used for infomration gathering later and i can keep the 
             #ec2 tests blocks consistent across modules

             ('DescribeExportTasks', 'describe_export_tasks', (), {}, ),
             ('DescribeFlowLogs', 'describe_flow_logs', (), {}, ),
             ('DescribeHostReservations', 'describe_host_reservations', (), {}, ),
             ('DescribeHosts', 'describe_hosts', (), {}, ),
             ('DescribeIamInstanceProfileAssociations', 'describe_iam_instance_profile_associations', (), {}, ),
             ('DescribeImportImageTasks', 'describe_import_image_tasks', (), {'DryRun':True}, ),
             ('DescribeImportSnapshotTasks', 'describe_import_snapshot_tasks', (), {'DryRun':True}, ),
             ('DescribeInternetGateways', 'describe_internet_gateways', (), {'DryRun':True}, ),
             ('DescribeKeyPairs', 'describe_key_pairs', (), {'DryRun':True}, ),
             ('CreateKeyPair', 'create_key_pair', (), {'KeyName':'asdfg12345','DryRun':True}, ),
             ('DescribeMovingAddresses', 'describe_moving_addresses', (), {'DryRun':True}, ),
             ('DescribeNatGateways', 'describe_nat_gateways', (), {}, ),
             ('DescribeNetworkAcls', 'describe_network_acls', (), {'DryRun':True}, ),
             ('DescribeNetworkInterfaces', 'describe_network_interfaces', (), {'DryRun':True}, ),
             ('DescribePlacementGroups', 'describe_placement_groups', (), {'DryRun':True}, ),
             ('DescribePrefixLists', 'describe_prefix_lists', (), {'DryRun':True}, ),
             ('DescribeReservedInstances', 'describe_reserved_instances', (), {'DryRun':True}, ),
             ('DescribeReservedInstancesListings', 'describe_reserved_instances_listings', (), {}, ),
             ('DescribeReservedInstancesModifications', 'describe_reserved_instances_modifications', (), {}, ),
             ('DescribeRouteTables', 'describe_route_tables', (), {'DryRun':True}, ),
             ('DescribeScheduledInstances', 'describe_scheduled_instances', (), {'DryRun':True}, ),
             ('DescribeSecurityGroups', 'describe_security_groups', (), {'DryRun':True}, ),
             ('DescribeSpotDatafeedSubscription', 'describe_spot_datafeed_subscription', (), {'DryRun':True}, ),
             ('DescribeSubnets', 'describe_subnets', (), {'DryRun':True}, ),
             ('DescribeTags', 'describe_tags', (), {'DryRun':True}, ),
             ('DescribeVolumeStatus', 'describe_volume_status', (), {'DryRun':True}, ),
             ('DescribeVpcClassicLink', 'describe_vpc_classic_link', (), {'DryRun':True}, ),
             ('DescribeVpcClassicLinkDnsSupport', 'describe_vpc_classic_link_dns_support', (), {}, ),
             ('DescribeVpcEndpointServices', 'describe_vpc_endpoint_services', (), {'DryRun':True}, ),
             ('DescribeVpcEndpoints', 'describe_vpc_endpoints', (), {'DryRun':True}, ),
             ('DescribeVpcPeeringConnections', 'describe_vpc_peering_connections', (), {'DryRun':True}, ),
             ('DescribeVpcs', 'describe_vpcs', (), {'DryRun':True}, ),
             ('CreateVpc', 'create_vpc', (), {'CidrBlock':'10.0.0.0/16','DryRun':True}, ),
             ('DescribeVpnConnections', 'describe_vpn_connections', (), {'DryRun':True}, ),
             ('DescribeVpnGateways', 'describe_vpn_gateways', (), {'DryRun':True}, ),
             ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'ec2', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/ecr.html
def brute_ecr_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating EC2 Container Registry (ECR) Permissions ###")
    tests = [('DescribeRepositories', 'describe_repositories', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'ecr', tests) 

#http://boto3.readthedocs.io/en/latest/reference/services/ecs.html
def brute_ecs_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating EC2 Container Service (ECS) Permissions ###")
    tests = [('ListClusters', 'list_clusters', (), {}),
             ('DescribeClusters', 'describe_clusters', (), {}),
             ('ListContainerInstances', 'list_container_instances', (), {}),
             ('ListTaskDefinitions', 'list_task_definitions', (), {}),
             ('ListTasks', 'list_tasks', (), {}), #needs a cluster name
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'ecs', tests) 

#http://boto3.readthedocs.io/en/latest/reference/services/efs.html
def brute_efs_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Elastic File System (EFS) Permissions ###")
    tests = [('DescribeFileSystems', 'describe_file_systems', (), {}),
             ('DescribeMountTargets', 'describe_mount_targets', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'efs', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/elasticache.html
def brute_elasticache_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ElastiCache Permissions ###")
    tests = [('DescribeCacheClusters', 'describe_cache_clusters', (), {}),
             ('DescribeCacheEngineVersions', 'describe_cache_engine_versions', (), {}), 
             ('DescribeCacheSecurityGroups', 'describe_cache_security_groups', (), {}),  
             ('DescribeCacheSubnetGroups', 'describe_cache_subnet_groups', (), {}),  
             ('DescribeEvents', 'describe_events', (), {}),
             ('DescribeReplicationGroups', 'describe_replication_groups', (), {}),  
             ('DescribeReservedCacheNodes', 'describe_reserved_cache_nodes', (), {}),
             ('DescribeReservedCacheNodesOfferings', 'describe_reserved_cache_nodes_offerings', (), {}),
             ('DescribeSnapshots', 'describe_snapshots', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'elasticache', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/elasticbeanstalk.html
def brute_elasticbeanstalk_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ElasticBeanstalk Permissions ###")
    tests = [('DescribeApplications', 'describe_applications', (), {}, ),
             ('DescribeApplicationVersions', 'describe_application_versions', (), {}),
             ('DescribeConfigurationOptions', 'describe_configuration_options', (), {}),
             ('DescribeEnvironments', 'describe_environments', (), {}),
             ('DescribeEnvironmentHealth', 'describe_environment_health', (), {}, ),
             ('DescribeEnvironmentManagedActionHistory', 'describe_environment_managed_action_history', (), {}),
             ('DescribeEnvironmentManagedActions', 'describe_environment_managed_actions', (), {}),
             ('DescribeEvents', 'describe_events', (), {}),
             ('DescribeInstancesHealth', 'describe_instances_health', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'elasticbeanstalk', tests)

def brute_elastictranscoder_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ElasticTranscoder Permissions ###")
    tests = [('ListPipelines', 'list_pipelines', (), {}),
             ('ListPresets', 'list_presets', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'elastictranscoder', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/elb.html
def brute_elasticloadbalancing_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ElasticLoadBalancing Permissions ###")
    tests = [('DescribeLoadBalancers', 'describe_load_balancers', (), {}), 
             ('DescribeAccountLimits', 'describe_account_limits', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'elb', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/elbv2.html
def brute_elasticloadbalancingv2_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating ElasticLoadBalancing Permissions ###")
    tests = [('DescribeLoadBalancers', 'describe_load_balancers', (), {}), 
             ('DescribeAccountLimits', 'describe_account_limits', (), {}),
             ('DescribeListeners', 'describe_listeners', (), {}),
             ('DescribeTargetGroups', 'describe_target_groups', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'elbv2', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/emr.html
def brute_emr_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Elastic MapReduce (EMR) Permissions ###")
    tests = [('ListClusters', 'list_clusters', (), {}), 
             ('ListSecurityConfigurations', 'list_security_configurations', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'emr', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/es.html
def brute_es_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Elasticsearch Service Permissions ###")
    tests = [('ListDomainNames', 'list_domain_names', (), {}), 
             ('ListElasticsearchVersions', 'list_elasticsearch_versions', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'es', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/events.html
def brute_cloudwatchevents_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating CloudWatch Events Permissions ###")
    tests = [('ListRules', 'list_rules', (), {}), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'events', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/firehose.html
def brute_firehose_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Kinesis Firehose Permissions ###")
    tests = [('ListDeliveryStreams', 'list_delivery_streams', (), {}), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'firehose', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/gamelift.html
def brute_gamelift_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating GameLift Permissions ###")
    tests = [('ListAliases', 'list_aliases', (), {}), 
             ('ListBuilds', 'list_builds', (), {}),
             ('ListFleets', 'list_fleets', (), {}), 
             ('DescribeEC2InstanceLimits', 'describe_ec2_instance_limits', (), {}),
             ('DescribeFleetAttributes', 'describe_fleet_attributes', (), {}),  
             ('DescribeFleetCapacity', 'describe_fleet_capacity', (), {}),  
             ('DescribeGameSessionDetails', 'describe_game_session_details', (), {}), 
             ('DescribeGameSessionQueues', 'describe_game_session_queues', (), {}),  
             ('DescribeGameSessions', 'describe_game_sessions', (), {}),  
             ('DescribePlayerSessions', 'describe_player_sessions', (), {}), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'gamelift', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/glacier.html
def brute_glacier_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Glacier Permissions ###")
    tests = [('ListVaults', 'list_vaults', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'glacier', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/greengrass.html
#TODO  #doesnt seem to be in the codebase for python ??
def brute_greengrass_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Greegrass Permissions ###")
    tests = [('ListGroups', 'list_groups', (), {}),
             ('ListLoggerDefinitions', 'list_logger_definitions', (), {}),
             ('ListSubscriptionDefinitions', 'list_subscription_definitions', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'greengrass', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/health.html
def brute_health_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Health Permissions ###")
    tests = [('DescribeEvents', 'describe_events', (), {}),
             ('DescribeEntityAggregates', 'describe_entity_aggregates', (), {}),
             ('DescribeEventTypes', 'describe_event_types', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'health', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/iam.html
#TODO chop out the ARN/username and make some more fun function calls must chop up ARN to get username
def brute_iam_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating IAM Permissions ###")
    #account_username = get_username(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    tests = [('GetUser', 'get_user', (), {} ), 
             #('ListUserPolicies', 'list_user_policies', (), {'UserName':'root'} ),
             ('ListGroups', 'list_groups', (), {} ),
             #('ListGroupsForUser', 'list_groups_for_user', (), {'UserName':account_username} ),
             ('GetCredentialReport', 'get_credential_report', (), {}) , 
             ('GetAccountSummary', 'get_account_summary', (), {} ),  
             ('GetAccountAuthorizationDetails', 'get_account_authorization_details', (), {} ), 
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'iam', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/importexport.html
def brute_importexport_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Import/Export Permissions ###")
    tests = [('ListJobs', 'list_jobs', (), {} ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'importexport', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/inspector.html
def brute_inspector_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Inspector Permissions ###")
    tests = [('ListFindings', 'list_findings', (), {} ),
             ('ListEventSubscriptions', 'list_event_subscriptions', (), {} ), 
             ('ListAssessmentRuns', 'list_assessment_runs', (), {} ),
             ('ListAssessmentTargets', 'list_assessment_targets', (), {} ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'inspector', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/iot.html
def brute_iot_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating IoT Permissions ###")
    tests = [('ListThings', 'list_things', (), {} ),
             ('ListPolicies', 'list_policies', (), {} ), 
             ('ListCertificates', 'list_certificates', (), {} ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'iot', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/iot-data.html
#NO functions to call without data
def brute_iotdata_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating IoT Data Plane Permissions ###")
    tests = [('', '', (), {} ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'iot-data', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/kinesis.html
def brute_kinesis_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Kinesis Permissions ###")
    tests = [('ListStreams', 'list_streams', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'kinesis', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/kinesisanalytics.html
def brute_kinesisanalytics_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Kinesis Analytics Permissions ###")
    tests = [('ListApplications', 'list_applications', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'kinesisanalytics', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/kms.html
def brute_kms_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Key Management Service (KMS) Permissions ###")
    tests = [('ListKeys', 'list_keys', (), {}),
             ('ListAliases', 'list_aliases', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'kms', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/lambda.html
def brute_lambda_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Lambda Permissions ###")
    tests = [('ListFunctions', 'list_functions', (), {}, ),
             ('ListEventSourceMappings', 'list_event_source_mappings', (), {}, ),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'lambda', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/lex-models.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/lex-runtime.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/lightsail.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/logs.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/machinelearning.html
#http://docs.aws.amazon.com/general/latest/gr/rande.html#machinelearning_region <--allows regions for ML
def brute_machinelearning_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Machine Learning Permissions ###")
    tests = [('DescribeDataSources', 'describe_data_sources', (), {}), 
             ('DescribeEvaluations', 'describe_evaluations', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'machinelearning', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/marketplace-entitlement.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/marketplacecommerceanalytics.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/meteringmarketplace.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/mturk.html
#TODO
def brute_mturk_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Mechanical Turk (MTurk) Permissions ###")
    tests = [('GetAccountBalance', 'get_account_balance', (), {}), 
             ('ListHits', 'list_hits', (), {}), 
             ('ListWorkerBlocks', 'list_worker_blocks', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'mturk', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/opsworks.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/opsworkscm.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/organizations.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/pinpoint.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/polly.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/rds.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/redshift.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/rekognition.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/resourcegroupstaggingapi.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/route53.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/route53domains.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/s3.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/sdb.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/servicecatalog.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/ses.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/shield.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/sms.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/snowball.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/sns.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/sqs.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/ssm.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/stepfunctions.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/storagegateway.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/sts.html
def brute_sts_permissions(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    print ("### Enumerating Security Token Service (STS) Permissions ###")
    tests = [('GetCallerIdentity', 'get_caller_identity', (), {}),
            ]
    return generic_permission_bruteforcer(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 'sts', tests)

#http://boto3.readthedocs.io/en/latest/reference/services/support.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/swf.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/waf.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/waf-regional.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/workdocs.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/workspaces.html
#TODO

#http://boto3.readthedocs.io/en/latest/reference/services/xray.html
#TODO






