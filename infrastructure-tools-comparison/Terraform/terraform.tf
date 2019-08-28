##
## Creates a set of users, assigns them to groups, and grants those groups
## permission to assume roles in associated accounts. 
## 

provider "aws" {}

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
  count = length(var.users)
  name  = "${var.users[count.index]}"
  force_destroy = true
}

resource "aws_iam_user_policy_attachment" "base_user_policy_attachment" {
  count      = length(var.users)
  user       = "${var.users[count.index]}"
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/BasicUserPolicy"
}

##
## Group creation
##

resource "aws_iam_group" "groups" {
  count = length(var.groups)
  name = "${var.groups[count.index]}"
}

##
## Group membership
##

resource "aws_iam_user_group_membership" "group-membership" {
  count = length(var.users)
  user  = "${var.users[count.index]}"
  groups = "${var.group_members[var.users[count.index]]}"
}

##
## Permission assignment
##

data "aws_iam_policy_document" "group-policies" {
  count = length(var.groups)
  statement {
    sid = "1"
    actions = [
        "sts:AssumeRole"
    ]
    resources = [
      for acct_role in var.group_permissions[var.groups[count.index]]:
        "arn:aws:iam::${var.account_id_lookup[acct_role[0]]}:role/${acct_role[1]}"
    ]
  }
}

resource "aws_iam_group_policy" "group-policies" {
  count = length(var.groups)
  name = "group-policies-${count.index}"
  group = "${var.groups[count.index]}"
  policy = "${data.aws_iam_policy_document.group-policies[count.index].json}" 
}
