
---

# User_input

Google form
Q1 input avatar url(Must)
Q2 input item url(Must)
Q3 input your twitter_id(Must)
Q4 input your desired price(Optional)
Q5 your desired hitaiou_worker_name(Optional)

output
df
avatar_url,item_url,twitter_id_desired_price,hitaiou_worker_name

---

# DataProcessing

columns Q1 and Q2
https://{shop_id}.booth.pm/
https://booth.pm/{language}/items/{item_id}
https://{shop_id}.booth.pm/items/{item_id}

if items/{item_id} is in Q1(avatar_url), is_avatar is 1.
if items/{item_id} is in Q2(avatar_url), is_avatar is 0.

output
df
avatar_url,item_url,twitter_id_desired_price,hitaiou_worker_name,shop_id,item_id,is_avatar


master_item
shop,item,avatar
vagrant,6082952,0
mukumi,5813187,1

Demand_ranking(sort by PotentialSales(highest first))
avatar,item,number_of_requests,median_desired_price,PotentialSales
5813187,6082952,8,1500,number_of_requests times median_desired_price

---

Users input google form
Users and hitaiou_workers can see Demand_ranking in dashboard


これを実現するコードを書いてください。

