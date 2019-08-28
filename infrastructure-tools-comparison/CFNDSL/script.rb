##
## Generates a template that will create a set of users, assign them to groups, and grant
## those groups permission to assume roles in associated accounts. 
##

require 'json'

users = [ "user1", "user2", "user3" ]

groups = [ "group1", "group2" ]

group_members = {
  "user1"  => [ "group1", "group2" ],
  "user2"  => [ "group1" ],
  "user3"  => [ "group2" ]
}

account_lookup = {
  "dev"   => "123456789012",
  "prod"  => "234567890123"
}

group_permissions = {
  "group1"  => [
                  [ "dev",    "FooAppDeveloper" ],
                  [ "prod",   "FooAppReadOnly" ]
               ],
  "group2"  => [
                  [ "dev",    "BarAppDeveloper" ],
                  [ "prod",   "BarAppReadOnly" ]
               ]
}


CloudFormation do
  Description "Manages the account's users"

  users.each do |user|
    IAM_User("#{user}") do
      UserName            user
      ManagedPolicyArns   [ FnSub("arn:aws:iam::${AWS::AccountId}:policy/BasicUserPolicy") ]
      Groups              group_members[user].map { |group| Ref("#{group}") }
    end
  end

  groups.each do |group|
    IAM_Group("#{group}") do
      GroupName group
    end

    policy_document = {
      "Version"   => "2012-10-17",
      "Statement" => [{
        "Effect"    => "Allow",
        "Action"    => [ "sts:AssumeRole" ],
        "Resource"  => group_permissions[group].map { |acct_role|
                        account_id = account_lookup[acct_role[0]]
                        role_name = acct_role[1]
                        "arn:aws:iam::#{account_id}:role/#{role_name}"
                       }
      }]
    }.to_json

    IAM_Policy("#{group}Policy") do
      PolicyName      "#{group}-AssumeRolePolicy"
      PolicyDocument  policy_document
      Groups          [ group ]
    end
  end
end
