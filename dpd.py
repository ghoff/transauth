from bitstring import BitString as Bits

# Densely Packed Decimal based on specification at
# from http://speleotrove.com/decimal/DPDecimal.html


def bcd2dpd(bcd):
	a,b,c,d,e,f,g,h,i,j,k,m = map((lambda x: bcd[x]),range(0,12))
	p=b | (a & j) | (a & f & i)
	q=c | (a & k) | (a & g & i)
	r=d
	s=(f & (~a | ~i)) | (~a & e & j) | (e & i)
	t=g  | (~a & e &k) | (a & i)
	u=h
	v=a | e | i
	w=a | (e & i) | (~e & j)
	x=e | (a & i) | (~a & k)
	y=m
	dpd = p+q+r+s+t+u+v+w+x+y
	return dpd


def dpd2bcd(dpd):
	p,q,r,s,t,u,v,w,x,y=map((lambda x: dpd[x]),range(0,10))
	a= (v & w) & (~s | t | ~x)
	b=p & (~v | ~w | (s & ~t & x))
	c=q & (~v | ~w | (s & ~t & x))
	d=r
	e=v & ((~w & x) | (~t & x) | (s & x))
	f=(s & (~v | ~x)) | (p & ~s & t & v & w & x)
	g=(t & (~v | ~x)) | (q & ~s & t & w)
	h=u
	i=v & ((~w & ~x) | (w & x & (s | t)))
	j=(~v & w) | (s & v & ~w & x) | (p & w & (~x | (~s & ~t)))
	k=(~v & x) | (t & ~w & x) | (q & v & w & (~x | (~s & ~t)))
	m=y
	bcd = a+b+c+d+e+f+g+h+i+j+k+m
	return bcd


def dpdpack(data):
	datalen = len(data)
	extra = 3-(datalen%3)
	input = Bits('0x'+'0'*extra+data)
	output = Bits()
	for i in range(0,len(input),12):
		output = output + bcd2dpd(input[i:i+12])
	if extra == 1:
		result = output[3:].hex
	elif extra == 2:
		result = output[6:].hex
	else:
		result = output.hex
	#remove leading 0x without stripping 0s that follow
	return result[2:]
	
	
def dpdunpack(data):
	input=Bits('0x'+data)
	extralen = len(input)%10
	if extralen != 0:
		extra = input[:extralen]
		input = input[extralen:]
		output = dpd2bcd(Bits('0b'+'0'*(10-extralen))+extra)
		if extralen == 4:
			output = output[-4:]
		if extralen == 7:
			output = output[-8:]
	else:
		output = Bits()
	for i in range(0,len(input),10):
		output += dpd2bcd(input[i:i+10])
	#remove leading 0x
	return output.hex[2:]
	

if __name__ == '__main__':
	data = '1234567890123456789012345678901'
	data = '4000100020003000123456789011234'
	data = '9999999999999999999999999999999'
	data = '7777777777777777777777777777777'
	print "datalen = %d" % len(data)
	print data
	output = dpdpack(data)
	print "outputlen = %d" % len(output)
	print output
	input = dpdunpack(output)
	print "origlen = %d" % len(input)
	print input
