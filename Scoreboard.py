score = []
with open("scores.txt") as f:
	for i, line in enumerate(f):
		score.append(int(line))

score.sort(reverse=True)
a = score[0]
b = score[1]
c = score[2]
d = score[3]
e = score[4]
f = score[5]
g = score[6]
h = score[7]
i = score[8]
j = score[9]
print"!<!Top Scores!>!"
print"1st",a
print"2nd",b
print"3rd",c
print"4th",d
print"5th",e
print"6th",f
print"7th",g
print"8th",h
print"9th",i
print"10th",j