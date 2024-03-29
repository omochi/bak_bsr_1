# Don't use this

From a result of using in production, it is revealed that this implementation does not concert with git storage strategy.
Many useless data transfer occured.

# bsr

Bsr is simple client-server model version management system constructed on git commands.

Name is comming from **B**inary **S**to**R**age.

Bsr is focused on portability.
It is written in python2 and implemented by git commands.
Source code is small.

# setup

## install

~~~
$ curl -s https://raw.githubusercontent.com/omochi/bsr/master/src/installer.bash | bash
~~~

You can install it any place you want to do.
Get this repository and add `src/bsr` to `PATH` or create symbolic link to `src/bsr` at directory belonging `PATH` .

## uninstall

~~~
$ rm -rf /usr/local/lib/bsr /usr/local/bin/bsr
~~~

## upgrade

~~~
$ cd /usr/local/lib/bsr
$ git pull
$ src/install.bash
~~~

# using

## initialize repository

~~~
$ git init
$ bsr init
~~~

## get version list

~~~
$ bsr versions
~~~

## checkout version

~~~
$ bsr checkout [<version>]
~~~

If you do not specify version, it means latest.

## push new version

~~~
$ (work with something)
$ bsr push
~~~

## delete old versions to keep repository size small

~~~
$ bsr delete <version>
~~~

# access rights control

Use unix user system same as git repository access control.

# use for application resource repository

Treat bsr repository as git submodule of application repository.

# hook function

Bsr has hook plugin function like git hook.
But in contrast git, bsr hooks is managed by bsr itself.
So you can share hooks of repository with your collaborators.

Hook scripts are put in directory `.bsr/hook/<hook-types>`.
These directories is created by `$ bsr init`.
Multiple scripts can be used in same hook type.

All hook types are below.

- pre push
- post checkout

# architecture

Versions are commits pointed by git tag.
They are independent commits and not connected with relationship between parent and child.
Each version commits are root commit in git.
So we can purge old version easily by erase tag and git treat files in version as unreachable garbage object.
