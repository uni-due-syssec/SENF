##Significance
#Mann-Whitney-U test
X <- c(RUNTIMES_A)
Y <- c(RUNTIMES_B)
w <- wilcox.test(X,Y)
print(w)

#Fisher exact test
a <- NUMBER_OF_CRASHES_A
b <- NUMBER_OF_CRASHES_B

n <- NUMBER_OF_RUNS
m <- matrix(c(a,n-a,b,n-b),2,2)
z <- fisher.test(m)
print(z)

##Effect size
# Odds ratio
rho <- 0.5
temp_or1 <- a+rho
temp_or2 <- n+rho-a
temp_or3 <- b+rho
temp_or4 <- n+rho-b
or_ab <- (temp_or1/temp_or2)/(temp_or3/temp_or4)
print(paste0("Odds ratio = ", or_ab))

#A12
Vardel <- function(X,Y){
	rank_sum <- sum(rank(c(X,Y))[seq_along(X)])
	result <- ((rank_sum/as.double(length(X)))-((as.double(length(X))+1)/2))/as.double(length(Y))
	return(result)
}

print(paste0("A12 = ", Vardel(X,Y)))
print("")

