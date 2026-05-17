import csv
import random

categories = ['family', 'friend_chat', 'student', 'office', 'delivery', 'shopping', 'travel', 'food', 'banking', 'customer_support', 'cab_service', 'courier', 'college', 'gaming', 'personal']

en_templates = {
    'family': ["arey yaar tu kaahan hai abhi kaisa hai sab", "bhaiyo aur bahno ko hello bolo wo bohot miss kar rahe hain", "mummy ne poocha tu kab ghar aayega khaana banaya hai", "papa bol rahe hain office se jaldi aana kuch kaam hai", "dadaji phone pe bohot khush hue teri awaaz sunke", "arey behen tu exam ki preparation kaisi chal rahi hai", "chacha ji ne poocha tumhara number kahaan se mila", "mausi ne naya ghar shuru kiya hai party de rahi hai", "papa ne kaha bus ticket book kar lo weekend ke liye", "arey didi tu office se late aati hai kya khana banaogi"],
    'friend_chat': ["bhai kya haal hai kahan fase hue ho", "arey yaar kal movie dekhne chalte hain kaisa rahega", "tu canteen mein aaja coffee peete hain", "bhai tune naya phone liya kitna price aaya", "arey yaar placement ka result aaya pakka milgaya", "kal raat ko group mein baat karte hain bhookhe mat raho", "tu sports ground aaja cricket khelenge", "arey last semester ka result dekh liya tu topper ban gaya", "bhai library mein seat mili main bhi aana chahta hoon"],
    'student': ["professor ne assignment last date badha diya hai", "arey exam timetable aaya hai preparation shuru karo", "library mein seats milna mushkil ho gaya yaar", "tu chemistry ki notes share kar sakta hai", "bhai marks aaye hain portal pe check kar le", "arey sem fees online submit karni hai last date kal hai", "tu placement cell mein gaye interview dates aaye hain", "bhai project report deadline miss ho gaya", "arey mess ka food bohot kharab ho gaya hai", "tu hostel room change ke liye apply kiya"],
    'office': ["good morning sir meeting 3 baje hai", "arey report submit kar diya email bhej diya hai", "bhai client se call aaya presentation ready karo", "tu leaves ke liye application bhejna hr ne kaha", "arey project deadline this week hai machao", "sir ne naya task assign kiya hai assign kar diya", "bhai work from home ki permission mil gayi hai", "arey team meeting mein sabko invite kar diya", "tu performance review ke liye prepare karo date fix hai", "sir ne appreciation kiya project ke liye bohot khush hai"],
    'delivery': ["arey delivery boy bahar khada hai door open karo", "bhai order cancel karna hai koi issue hai", "tu order ki track kar sakta hai kahan phas gaya", "arey delivery time 10 minutes mein aayega wait karo", "package thoda damage ho gaya hai return policy check karo", "bhai cod hai ya online payment karni hai", "arey wrong item deliver ho gaya hai exchange karana hai", "order delivered successfully photo leke rakha hai", "bhai delivery partner ne call kiya location confirm karo"],
    'shopping': ["arey sale mein bohot sasta mil raha hai shopping karo", "bhai online store pe discount code chal raha hai", "tu clothes ka size check kar exchange possible hai", "arey shoe ka colour nahi pasand return karna hai", "bhai cashback offer mil raha hai payment karo", "arey wallet ki payment fail ho gayi retry karo", "tu gift wrapping karwa sakte ho birthday gift hai", "bhai order placed ho gaya confirmation email aaya", "arey product out of stock hai notify kar denge"],
    'travel': ["arey flight booking confirm ho gayi pnr bhej diya", "bhai train ki waiting list confirm ho gayi", "tu hotel reservation kar liya checkin time dekho", "arey cab booked hai driver 10 minute mein aayega", "bhai travel insurance ka option hai lena chahiye", "arey boarding pass print karna hai kiosk available hai", "tu baggage allowance check kiya extra ka charge lagega", "bhai visa application status online check kar sakte hain", "arey refund mil gaya flight cancellation ke baad"],
    'food': ["arey zomato se order kiya 30 minute mein aayega", "bhai swiggy par discounts chal rahe hain try karo", "tu restaurant mein table book kiya confirm aaya", "arey biryani ka order place kiya jaldi aayega", "bhai buffet mein sabziyo ki variety bohot achhi hai", "arey tiffin service ki trial le raha hai first day hai", "tu home delivery ka time prefer karta hai", "bhai chinese restaurant ka recommendation chahiye", "arey cake order kiya birthday ke liye timing correct hai"],
    'banking': ["arey bank ne new policy introduce kiya hai", "bhai atm ka pin change karna hai kaise karte hain", "tu online banking activate kiya secure hai", "arey account statement download kar liya verify karo", "bhai credit card ka bill due hai payment karo", "arey loan application ke liye documents submit kiye", "tu fd ka interest rate check kiya better option hai", "bhai net banking password reset kar raha hai", "arey debit card blocked ho gaya new card manga"],
    'customer_support': ["arey customer care se baat karni hai representative chahiye", "bhai service request register kiya ticket number mil gaya", "tu refund status check kar sakta hai", "arey warranty claim karni hai process batayo", "bhai subscription renew karni hai payment options batado", "arey product defect ki complaint kar raha hoon", "tu chat support use kar sakte ho quick response milta hai", "bhai service charge ki details chahiye breakdown do", "arey installation appointment book karni hai"],
    'cab_service': ["arey cab booked hai driver 5 minute mein aayega", "bhai ride cancel karni hai reason select karo", "tu driver ko call kar sakta hai pickup point confirm karo", "arey ride fare estimate dekho meter se kam aayega", "bhai ride completed rating dena mat bhoolna", "arey extra stops add karni hai driver se baat karo", "tu outstation ride ke liye package check karo", "bhai cab type select karo sedan ya suv", "arey driver ne route change kiya reason pocho"],
    'courier': ["arey courier booked hai pickup tomorrow aayega", "bhai tracking number check karo live location dekho", "tu package deliver kar diya receiver ne sign kiya", "arey delivery delayed hai weather ke karan hai", "bhai international shipping ka charges calculate karo", "arey fragile item hai proper packing karo", "courier boy ne call kiya address confirm karo", "bhai order ki delivery 2 days mein hogi", "arey wrong address diya hai correction karo"],
    'college': ["arey college fest mein participation karni hai", "bhai attendance percentage maintain karna hai", "tu club meetings mein attend karta hai", "arey college bus route check kiya timing dekho", "bhai semester registration last week hai form fill karo", "arey library card renew karni hai last date kal hai", "tu college canteen ka food card recharge kiya", "bhai department mein seminar hai attendance mandatory hai", "arey alumni meet ke liye registration open hai"],
    'gaming': ["arey bgmi mein squad match khelenge", "bhai free fire ka new event shuru ho gaya hai", "tu cs go mein rank improve kiya", "arey valorant ka new agent aaya hai try kiya", "bhai pubg mobile mein season reset ho gaya", "arey gaming phone lena chahiye performance better hai", "tu steam sale mein game khareeda discount mila", "bhai online tournament mein register kiya", "arey gaming headphones ki recommendation chahiye"],
    'personal': ["arey kaisa hai tu koi update hai", "bhai kaal se call nahi hui busy tha kya", "tu apna time manage kar raha hai schedule banao", "arey future ki planning kar raha hoon suggestions chahiye", "bhai health checkup karaya report aayi hai", "arey new hobby shuru karni hai kya suggest karoge", "tu self improvement ke liye kya kar raha hai", "bhai meditation shuru kiya mental health important hai", "arey daily routine maintain kar raha hoon disciplined hoon"]
}

hi_templates = {
    'family': ["abhi kaun sa time ho raha hai", "ghar wapas kab aoge", "mummy ne khana banaaya hai", "papa ka phone answering nahi ho raha", "dada ji ki health theek hai", "behen ki shaadi ki taiyari kaise chal rahi hai", "chacha ji ne poochha aapka number", "bhai log bahut miss kar rahe hain", "nani ji ne bahut yaad kiya", "arey behen ka exam kab hai"],
    'friend_chat': ["kal raat ki party mein aoge", "tu kaha busy hai itna", "movie dekhne chalte hain na", "cafe mein chill karne chalte hain", "bhai tune naya number save kiya kya", "placement ki news mil gayi", "sirf tum hi nahi sab missing kar rahe hain", "gym chalte hain aaj", "cricket match dekhne jaate hain"],
    'student': ["exam ka date sheet aaya hai", "assignment ki deadline badh gayi", "library mein jaldi jaana padega", "notes ki xerox karwani hai", "semester fee last date kal tak hai", "attendance ki problem ho gayi hai", "placement ki preparation shuru karo", "project ki presentation date confirm hui", "mess ka food bahut bekaar ho gaya"],
    'office': ["meeting mein attendance zaruri hai", "report ki last date aaj hai", "client se call aana chahiye", "boss ne naya kaam diya hai", "work from home ki request bhejni hai", "team ki performance improve karni hai", "salary slip download karni hai", "leave application submit karni hai", "project deadline aaj hai"],
    'delivery': ["delivery boy bahar khada hai", "order cancel karni hai", "tracking number check karna hai", "package thoda damage ho gaya hai", "wrong item deliver hua hai", "order confirm ho gaya hai", "delivery time 20 minute hai", "grocery items ka bill bana hai", "express delivery lena hai"],
    'shopping': ["sale mein bahut discount mil raha hai", "size exchange karni hai", "clothes ki quality theek nahi hai", "cashback offer chal raha hai", "gift wrapping karwaana hai", "order placed ho gaya hai", "product out of stock hai", "discount coupon apply karna hai", "payment failed ho gaya hai"],
    'travel': ["flight ka booking kar liya hai", "train ki waiting hat gayi", "hotel ki confirmation mail aayi", "cab ki booking kar li hai", "travel insurance lena hai", "boarding pass print karna hai", "baggage allowance check karni hai", "visa status online dekhna hai", "refund process ho raha hai"],
    'food': ["zomato se order kiya hai", "swiggy pe discount mil raha hai", "restaurant mein table book kiya hai", "biryani ka order kiya hai", "home delivery time confirm hai", "diet food order karni hai", "cake order kiya hai birthday ke liye", "thali ka menu dekhna hai", "combo meal lena hai"],
    'banking': ["atm pin change karni hai", "net banking activate karni hai", "account statement download karni hai", "credit card bill pay karna hai", "loan ke liye apply karna hai", "fd interest rate dekhna hai", "debit card blocked ho gaya hai", "upi payment karni hai", "bank branch jaana padega"],
    'customer_support': ["customer care se baat karni hai", "service request register karni hai", "refund status pochna hai", "warranty claim karni hai", "subscription renew karni hai", "complaint register karni hai", "technical help chahiye", "installation appointment lena hai", "return policy dekhni hai"],
    'cab_service': ["cab book kar liya hai", "ride cancel karni hai", "driver se call karni hai", "fare estimate dekhna hai", "ride complete ho gaya hai", "extra stops add karni hain", "outstation ride lena hai", "sedan book karna hai", "driver ne route change kiya"],
    'courier': ["courier book kar liya hai", "tracking number mil gaya hai", "delivery ho gaya hai", "delivery delayed hai", "shipping charges dekhne hain", "fragile item hai dhyan se pack karo", "pickup time confirm karni hai", "address correction karni hai", "insurance add karni hai"],
    'college': ["fest mein participate karna hai", "attendance maintain karni hai", "club meeting mein aana hai", "bus timing dekhni hai", "registration form fill karna hai", "library card renew karni hai", "mess menu change hua hai", "seminar mein attend karna hai", "sports trials hain"],
    'gaming': ["bgmi mein match khelna hai", "free fire ka new update aaya hai", "rank improve karni hai", "new agent try karna hai", "season reset ho gaya hai", "gaming setup upgrade karna hai", "steam sale chal raha hai", "tournament register karna hai", "headphones ki recommendation chahiye"],
    'personal': ["kaisa hai tu abhi", "call nahi aaya kya", "time schedule karna hai", "future planning kar raha hoon", "health checkup karaya hai", "hobby shuru karni hai", "self improvement karni hai", "meditation shuru kiya hai", "routine maintain kar raha hoon"]
}

rows = []
seen = set()

for cat in categories:
    for t in en_templates[cat]:
        if t.lower() not in seen:
            rows.append({'text': t.lower(), 'label': '0', 'category': cat, 'language': 'en', 'tactics': 'none'})
            seen.add(t.lower())

for cat in categories:
    for t in hi_templates[cat]:
        if t.lower() not in seen:
            rows.append({'text': t.lower(), 'label': '0', 'category': cat, 'language': 'hi', 'tactics': 'none'})
            seen.add(t.lower())

while len([r for r in rows if r['category']==cat and r['language']=='hinglish']) < 15:
    for cat in categories:
        texts = list(set(en_templates[cat] + hi_templates[cat]))
        t = random.choice(texts)
        words = t.split()
        random.shuffle(words)
        new_text = ' '.join(words)
        if new_text.lower() not in seen:
            rows.append({'text': new_text.lower(), 'label': '0', 'category': cat, 'language': 'hinglish', 'tactics': 'none'})
            seen.add(new_text.lower())

print(f"Generated {len(rows)} rows")

with open('./dataset/conversations.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['text', 'label', 'category', 'language', 'tactics'])
    w.writeheader()
    w.writerows(rows)

cats = {}
langs = {}
for r in rows:
    cats[r['category']] = cats.get(r['category'], 0) + 1
    langs[r['language']] = langs.get(r['language'], 0) + 1
print('Categories:', cats)
print('Languages:', langs)