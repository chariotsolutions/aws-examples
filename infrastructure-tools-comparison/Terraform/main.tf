##
## Creates a set of users, assigns them to groups, and grants those groups
## permission to assume roles in associated accounts. 
## 


terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}


##
## For this example, all configuration is hardcoded; could be replaced
## with external variable definitions
##


data "aws_caller_identity" "current" {}

variable "users" {
    type = list
    default = [ "user1", "user2", "user3" ]
}

variable "groups" {
    type = list
    default = [ "group1", "group2" ]
}

variable "group_members" {
    type = map(list(string))
    default = {
      "user1"  = [ "group1", "group2" ],
      "user2"  = [ "group1" ],
      "user3"  = [ "group2" ]
    }
}

variable "account_id_lookup" {
    type = map
    default = {
        "dev"   = "123456789012",
        "prod"  = "234567890123"
    }
}

variable "group_permissions" {
    type = map(list(list(string)))
    default = {
      "group1"  = [
                        [ "dev",    "FooAppDeveloper" ],
                        [ "prod",   "FooAppReadOnly" ]
                      ],
      "group2"  = [
                        [ "dev",    "BarAppDeveloper" ],
                        [ "prod",   "BarAppReadOnly" ]
                      ]
    }
}

##
## User creation
##

resource "aws_iam_user" "users" {
  for_each      = toset(var.users)
  name          = each.key
  force_destroy = true
}

resource "aws_iam_user_policy_attachment" "base_user_policy_attachment" {
  for_each      = toset(var.users)
  user          = each.key
  policy_arn    = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/BasicUserPolicy"
}

##
## Group creation
##

resource "aws_iam_group" "groups" {
  for_each  = toset(var.groups)
  name      = each.key
}

##
## Group membership
##

resource "aws_iam_user_group_membership" "group-membership" {
  for_each  = var.group_members
  user      = each.key
  groups    = each.value
}

##
## Permission assignment
##

data "aws_iam_policy_document" "group-policies" {
  for_each = var.group_permissions
  statement {
    sid         = "AssumeRole"
    actions     = [ "sts:AssumeRole" ]
    resources   = [
      for acct_role in each.value :
        "arn:aws:iam::${var.account_id_lookup[acct_role[0]]}:role/${acct_role[1]}"
    ]
  }
}

resource "aws_iam_group_policy" "group-policies" {
  for_each  = toset(var.groups)
  name      = "group-policies-${each.key}"
  group     = each.key
  policy    = data.aws_iam_policy_document.group-policies[each.key].json
}
