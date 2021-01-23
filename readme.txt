message
    text
    data

error
    text

exception
    text

object
	name
	input
		dimension
	data
	    actions
		fields
		data
	dimensions
		name
		fieldsets
			fields
			actions

queryset
	name
	input
		q
		subset
		sort
		page
		filter_1
		filter_2
		filter_n
	metadata
			search
			filters
			actions
			subsets
			display
	data

form
	name
	errors
	input
	metadata
		fields
			label
			type
			required
			mask
			value
			choices
			help
			width
			errors


statistic
	name
	series

pdfreport
	url



openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365