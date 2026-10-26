# M8.1 - AI Threat Model

## Pehle concepts samajh lein

- **Threat modeling**: defence lagane se PEHLE yeh socha samjha jaye ke app par
  kahan kahan se hamla ho sakta hai, kya qeemti cheezein hain, aur kaun sa
  attacker kaise nuqsan kar sakta hai. Yani "pehle naqsha banao, phir deewar lagao".

- **Attack surface**: woh saari jagahein jahan se bura data model tak pohanch
  sakta hai ya model nuqsan kar sakta hai (user message, retrieved docs, tool
  outputs, emails waghera). Jab model untrusted content parhe, private data tak
  pohanche, tools chalaye, ya actions le, to attack surface bar jata hai.

- **Asset**: woh qeemti cheez jise hum bachana chahte hain (doosron ka PII, paisa/
  refund, internal business data, prompt ke secrets, store ki reputation,
  availability/cost).

- **Actor**: koi bhi jo system se interact karta hai (honest customer, malicious
  customer, content attacker jo docs mein bura hukm daale, staff, model provider).

- **Trust boundary**: woh lakeer jahan bharosemand aur bina-bharose cheez milti
  hai. Har boundary par checking chahiye.

- **Model output is untrusted**: model ka chuna tool, arguments, SQL, URLs aur
  text sab "tajweez" hain, hukm nahi. Jin cheezon ka asar hota hai unhe normal
  code check kare, jise model baat karke na badal sake.

- **Lethal trifecta**: (1) untrusted input model tak, (2) private data / taqatwar
  tools, (3) data bahar bhejne ka raasta. Teeno ikatthe = ek injection bara nuqsan.

## Is folder mein

- `THREAT_MODEL.md` - TimeHouse app ka poora threat model: assets, actors, trust
  boundaries, lethal trifecta, 11 vulnerabilities (V1-V11), 8 attack scenarios
  (S1-S8), aur yeh plan ke kaunsa module kaunsi kamzori theek karega.

Is document ko pehle parhein; poore Level 8 ke saare modules isi par chalenge.
Har aage wale module ka code in V- aur S- numbers ko reference karta hai.
