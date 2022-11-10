import sys
import json
import time
import string
import requests
import argparse
import threading

# argparse bootstrap

parser = argparse.ArgumentParser(
	description="github email/name scraper using api, made with love by the one and only jade <3"
)

parser.add_argument(
	"--token", "-t", 
	type=str, 
	help="optional github access token, due to githubs ratelimiting (https://github.com/settings/tokens)"
)

parser.add_argument(
	"name", 
	type=str, 
	help="required github username"
)

arguments = parser.parse_args()

# helper functions

def throw(error):
	print(f"error - {error}")
	sys.exit(1)

def request(url):
	# optional authorization header
	header = { 
		"Authorization" : f"Bearer {arguments.token}" 
	}

	# get the data with the optional headers
	request = requests.get(url, headers = header) if arguments.token else requests.get(url)

	# parse and return data
	return json.loads(request.content)

def repo_worker(url, info):
	# get the commits of the repo
	commits_json = request(url)

	# i forget why but sometimes this doesnt return the desired data
	if type(commits_json) != list: return

	# iterate commits and the two fields that contain user info
	for commit in commits_json:	
		# iterate two fields with user info
		for user in ["author", "committer"]:
			# sometimes skip name checking
			check_name = True

			#iterate both fields
			for field in ["email", "name"]:
				valid = True
				
				# skip name sometimes bc its just annoying
				if field == "name" and not check_name:
					continue

				# check if github in field, if so just skip
				if "github" in commit["commit"][user][field].lower():
					valid = False

				# check for cases with commits from other github accs with same name
				if commit["author"] and commit["author"]["login"] != arguments.name and commit["commit"][user]["name"] not in info["name"]:
					check_name = valid = False

				# if not in table and info is valid add to table
				if valid and commit["commit"][user][field] not in info[field]: 
					info[field].append(commit["commit"][user][field])

if __name__ == "__main__":
	# get main api links
	api_json = request("https://api.github.com/")

	# determine if ratelimited
	if "message" in api_json:
		throw("ratelimted, try again with access token")

	# get repos
	repos_json = request(api_json["user_repositories_url"][:-26].format(user = arguments.name))

	# initialise lists
	info = {
		"name" : list(),
		"email" : list()
	}

	threads = list()

	# iterate repos
	for repo in repos_json:
		# if repo is a fork, then ignore it
		if repo["fork"]: continue

		# create thread
		thread = threading.Thread(target=repo_worker, args=(repo["commits_url"][:-6], info,))

		# add to threads list
		threads.append(thread)

		# start thread
		thread.start() 

	print(f"created {len(threads)} threads, waiting for execution to finish")

	# wait for threads to finish executing
	for thread in threads: thread.join()

	# output names and emails in list

	print("\nnames\n" + "-" * 20)
	for name in info["name"]: print(name)

	print("\nemails\n" + "-" * 20)
	for email in info["email"]: print(email)