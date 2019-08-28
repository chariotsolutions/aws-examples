import cdk = require('@aws-cdk/core');
import iam = require('@aws-cdk/aws-iam');


const userNames : string[] = [ "user1", "user2", "user3" ]

const groupNames : string[] = [ "group1", "group2" ]

const userGroups = new Map<string,string[]>()
userGroups.set("user1", [ "group1", "group2" ])
userGroups.set("user2", [ "group1" ])
userGroups.set("user3", [ "group2" ])

const accountIds = new Map<string,string>()
accountIds.set("dev",  "123456789012")
accountIds.set("prod", "234567890123")

const groupPermissions = new Map<string,Array<[string,string]>>()
groupPermissions.set("group1", [
    [ "dev",    "FooAppDeveloper" ],
    [ "prod",   "FooAppReadOnly" ]
])
groupPermissions.set("group2", [
    [ "dev",    "BarAppDeveloper" ],
    [ "prod",   "BarAppReadOnly" ]
])


export class UsersAndGroupsStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // since we're creating constructs inside functions, we can't use "this"
    let stack = this

    // these two maps let us retrieve constructs for later use
    let groupsByName = new Map<string,iam.Group>()
    let usersByName = new Map<string,iam.User>()

    groupNames.forEach(function(groupName) {
      const group = new iam.Group(stack, groupName, {
        groupName: groupName
      })
      groupsByName.set(groupName, group)
    })

    userNames.forEach(function(userName) {
      const user = new iam.User(stack, userName, {
        userName: userName
      })

      user.addManagedPolicy({
        managedPolicyArn: stack.formatArn({
          service:      "iam",
          region:       "",
          resource:     "policy",
          resourceName: "BasicUserPolicy"
        })
      })

      usersByName.set(userName, user)
    })

    userGroups.forEach(function(groupNames, userName) {
      const user  = usersByName.get(userName)
      groupNames.forEach(function(groupName) {
        const group = groupsByName.get(groupName)
        if (user && group) {
            user.addToGroup(group)
        }
      })
    })

    groupPermissions.forEach(function(roleSpecs, groupName) {
      let assumableRoles = roleSpecs.map(function([accountName, roleName]) {
        // use a default value to avoid explicit existence test ... should always be valid
        let accountId = accountIds.get(accountName) || ""
        return stack.formatArn({
          service:      "iam",
          region:       "",
          account:      accountId,
          resource:     "role",
          resourceName: roleName
        })
      })
      let policyStatement = new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [ "sts:AssumeRole" ],
        resources: assumableRoles
      })
      let group = groupsByName.get(groupName)
      if (group) {
        group.addToPolicy(policyStatement)
      }
    })
  }
}
