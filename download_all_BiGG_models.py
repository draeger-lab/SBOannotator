import requests
import json

###########################################
# Download all models from BiGG
###########################################

res = requests.get("http://bigg.ucsd.edu/api/v2/models/")
res_json = res.content.decode("utf-8")
info_i = json.loads(res_json)

for entry in info_i['results']:
    # download all models stored in BiGG automatically
    download = requests.get("http://bigg.ucsd.edu/static/models/"+entry['bigg_id']+".xml")
    # save model in directory
    open('models/'+entry['bigg_id']+'.xml', 'wb').write(download.content)
    print(entry['bigg_id'], 'done downloading')


